"""
Real-Time Multi-Depot Fleet Optimizer with GPS Telemetry & Live Traffic Ingestion
================================================================================
Features:
- Multi-Depot Dynamic Vehicle Routing with Capacity, Time-Window & HOS Constraints
- GPS Telemetry Ingestion with Anti-Spoofing & Teleportation Anomaly Filtering
- Dynamic Traffic Engine: Real-time congestion zones, traffic-aware travel times & delay impact
- Traffic-aware Dynamic Re-Routing & Inter-Depot Rebalancing
- System KPI & Constraint Violation Auditing
"""

import time
import math
import random
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional
from enum import Enum


# =====================================================================
# 1. DOMAIN MODELS & ENUMS
# =====================================================================

class VehicleStatus(Enum):
    IDLE = "IDLE"
    EN_ROUTE = "EN_ROUTE"
    SERVICING = "SERVICING"
    MAINTENANCE = "MAINTENANCE"


class TrafficSeverity(Enum):
    CLEAR = "CLEAR"         # 1.0x travel time (normal speed)
    MODERATE = "MODERATE"   # 1.4x travel time (-30% speed)
    HEAVY = "HEAVY"         # 2.2x travel time (-55% speed)
    GRIDLOCK = "GRIDLOCK"   # 3.5x travel time (-70% speed)

    @property
    def speed_multiplier(self) -> float:
        mapping = {
            TrafficSeverity.CLEAR: 1.0,
            TrafficSeverity.MODERATE: 0.70,
            TrafficSeverity.HEAVY: 0.45,
            TrafficSeverity.GRIDLOCK: 0.28,
        }
        return mapping[self]

    @property
    def delay_multiplier(self) -> float:
        return 1.0 / self.speed_multiplier


@dataclass
class Location:
    lat: float
    lon: float

    def distance_to(self, other: "Location") -> float:
        """Haversine distance estimation in kilometers."""
        R = 6371.0
        dlat = math.radians(other.lat - self.lat)
        dlon = math.radians(other.lon - self.lon)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(self.lat)) * math.cos(math.radians(other.lat)) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def bearing_to(self, other: "Location") -> float:
        """Calculates initial compass bearing (0-360 degrees) to another point."""
        lat1 = math.radians(self.lat)
        lat2 = math.radians(other.lat)
        diff_lon = math.radians(other.lon - self.lon)
        x = math.sin(diff_lon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diff_lon))
        initial_bearing = math.atan2(x, y)
        compass_bearing = (math.degrees(initial_bearing) + 360) % 360
        return compass_bearing


@dataclass
class Depot:
    id: str
    name: str
    location: Location
    rebalance_penalty_per_km: float = 1.5  # Cost penalty for ending route at foreign depot


@dataclass
class Order:
    id: str
    customer_name: str
    location: Location
    weight_kg: float
    volume_m3: float
    earliest_time: float      # Relative minutes from simulation epoch
    latest_time: float        # Must arrive before this time
    service_duration: float   # Unloading/signing time in minutes
    is_cancelled: bool = False


@dataclass
class DriverHOS:
    max_shift_minutes: float = 600.0     # 10 Hours max shift
    current_shift_minutes: float = 0.0
    max_driving_minutes: float = 480.0   # 8 Hours max continuous driving
    current_driving_minutes: float = 0.0


@dataclass
class GPSPing:
    vehicle_id: str
    location: Location
    timestamp: float
    speed_kmh: float = 0.0
    heading_deg: float = 0.0
    accuracy_m: float = 5.0


@dataclass
class Vehicle:
    id: str
    name: str
    home_depot_id: str
    current_depot_id: str
    current_location: Location
    max_weight_kg: float
    max_volume_m3: float
    cost_per_km: float
    hos: DriverHOS
    status: VehicleStatus = VehicleStatus.IDLE
    current_weight: float = 0.0
    current_volume: float = 0.0
    last_gps_ping: Optional[GPSPing] = None


@dataclass
class RouteNode:
    order: Optional[Order]        # None if Depot Node
    depot_id: Optional[str]
    location: Location
    arrival_time: float = 0.0     # Minutes from route start
    departure_time: float = 0.0   # Minutes from route start
    distance_from_prev: float = 0.0
    traffic_condition: TrafficSeverity = TrafficSeverity.CLEAR
    traffic_delay_min: float = 0.0


@dataclass
class Route:
    vehicle_id: str
    origin_depot_id: str
    destination_depot_id: str
    nodes: List[RouteNode] = field(default_factory=list)
    total_distance_km: float = 0.0
    total_cost: float = 0.0
    total_traffic_delay_min: float = 0.0


# =====================================================================
# 2. DYNAMIC TRAFFIC ENGINE
# =====================================================================

@dataclass
class TrafficIncident:
    id: str
    description: str
    center: Location
    radius_km: float
    severity: TrafficSeverity
    start_time: float
    duration_minutes: float


class TrafficEngine:
    """Simulates and evaluates dynamic real-time traffic congestion on route corridors."""

    def __init__(self, base_highway_speed: float = 65.0, base_city_speed: float = 40.0):
        self.base_highway_speed = base_highway_speed
        self.base_city_speed = base_city_speed
        self.active_incidents: Dict[str, TrafficIncident] = {}

    def report_incident(self, incident: TrafficIncident):
        self.active_incidents[incident.id] = incident

    def clear_incident(self, incident_id: str):
        self.active_incidents.pop(incident_id, None)

    def evaluate_corridor_traffic(self, origin: Location, destination: Location, current_time: float = 0.0) -> Tuple[TrafficSeverity, float]:
        """
        Determines the worst traffic severity and effective average speed along
        the straight-line corridor between two locations.
        """
        midpoint = Location(
            lat=(origin.lat + destination.lat) / 2.0,
            lon=(origin.lon + destination.lon) / 2.0
        )
        corridor_len = origin.distance_to(destination)
        worst_severity = TrafficSeverity.CLEAR

        for incident in self.active_incidents.values():
            if current_time < incident.start_time or current_time > (incident.start_time + incident.duration_minutes):
                continue

            # Distance from corridor points to incident center
            dist_origin = origin.distance_to(incident.center)
            dist_dest = destination.distance_to(incident.center)
            dist_mid = midpoint.distance_to(incident.center)

            min_dist = min(dist_origin, dist_dest, dist_mid)
            if min_dist <= incident.radius_km + (corridor_len * 0.25):
                if incident.severity.value == TrafficSeverity.GRIDLOCK.value:
                    worst_severity = TrafficSeverity.GRIDLOCK
                    break
                elif incident.severity.value == TrafficSeverity.HEAVY.value:
                    worst_severity = TrafficSeverity.HEAVY
                elif incident.severity.value == TrafficSeverity.MODERATE.value and worst_severity != TrafficSeverity.HEAVY:
                    worst_severity = TrafficSeverity.MODERATE

        base_speed = self.base_highway_speed if corridor_len > 15.0 else self.base_city_speed
        effective_speed = base_speed * worst_severity.speed_multiplier
        return worst_severity, effective_speed


# =====================================================================
# 3. GPS & ADVERSARIAL TELEMETRY INGESTION ENGINE
# =====================================================================

class TelemetryIngestor:
    """
    Ingests live vehicle GPS breadcrumbs, updates positions, and filters
    adversarial anomalies such as GPS spoofing, clock manipulation, & teleportation.
    """

    def __init__(self, max_speed_kmh: float = 130.0, max_jump_distance_km: float = 50.0):
        self.max_speed_kmh = max_speed_kmh
        self.max_jump_distance_km = max_jump_distance_km
        self.telemetry_history: Dict[str, List[GPSPing]] = {}

    def process_ping(self, ping: GPSPing) -> Tuple[bool, str]:
        history = self.telemetry_history.setdefault(ping.vehicle_id, [])

        if history:
            last_ping = history[-1]
            dt_seconds = ping.timestamp - last_ping.timestamp
            dt_hours = dt_seconds / 3600.0

            if dt_seconds <= 0:
                return False, f"REJECTED: Non-monotonic timestamp (delta {dt_seconds:.1f}s)."

            dist_km = last_ping.location.distance_to(ping.location)
            implied_speed = dist_km / max(dt_hours, 1e-6)

            # Check 1: Impossible physical speed (GPS Spoofing / Teleportation)
            if implied_speed > self.max_speed_kmh:
                return False, f"REJECTED: GPS Spoofing detected! Implied speed {implied_speed:.1f} km/h > limit {self.max_speed_kmh} km/h (moved {dist_km:.1f}km in {dt_seconds:.1f}s)."

            # Check 2: Unrealistic short-interval teleportation
            if dist_km > self.max_jump_distance_km and dt_seconds < 120.0:
                return False, f"REJECTED: Spatial Jump detected! Moved {dist_km:.1f}km in <2 minutes."

        history.append(ping)
        return True, "ACCEPTED: Valid Telemetry Ping."

    def get_latest_position(self, vehicle_id: str) -> Optional[GPSPing]:
        history = self.telemetry_history.get(vehicle_id)
        return history[-1] if history else None


# =====================================================================
# 4. TRAFFIC-AWARE DYNAMIC CONSTRAINT EVALUATOR
# =====================================================================

class ConstraintChecker:
    """Evaluates strict operational limitations across time, traffic delays, capacity, and HOS."""

    @staticmethod
    def validate_and_compute_schedule(
        route: Route,
        vehicle: Vehicle,
        depots: Dict[str, Depot],
        traffic_engine: TrafficEngine,
        start_time_offset: float = 0.0
    ) -> Tuple[bool, str, List[RouteNode], float, float]:
        """
        Validates constraints and computes exact node arrival/departure times
        factoring in dynamic traffic conditions.
        Returns: (is_valid, message, updated_nodes, total_distance, total_delay)
        """
        accumulated_weight = 0.0
        accumulated_volume = 0.0
        accumulated_driving_time = vehicle.hos.current_driving_minutes
        current_time = start_time_offset
        total_distance = 0.0
        total_delay = 0.0
        updated_nodes: List[RouteNode] = []

        for i, node in enumerate(route.nodes):
            new_node = RouteNode(
                order=node.order,
                depot_id=node.depot_id,
                location=node.location,
                arrival_time=current_time,
                departure_time=current_time,
                distance_from_prev=0.0,
                traffic_condition=TrafficSeverity.CLEAR,
                traffic_delay_min=0.0
            )

            if i > 0:
                prev_loc = updated_nodes[i - 1].location
                dist = prev_loc.distance_to(node.location)
                new_node.distance_from_prev = dist
                total_distance += dist

                # Evaluate corridor traffic
                traffic_cond, eff_speed = traffic_engine.evaluate_corridor_traffic(
                    prev_loc, node.location, current_time
                )
                new_node.traffic_condition = traffic_cond

                # Compute baseline vs traffic-delayed drive time
                base_drive_time = (dist / max(traffic_engine.base_city_speed, 1.0)) * 60.0
                actual_drive_time = (dist / max(eff_speed, 1.0)) * 60.0
                segment_delay = max(0.0, actual_drive_time - base_drive_time)

                new_node.traffic_delay_min = segment_delay
                total_delay += segment_delay

                current_time += actual_drive_time
                accumulated_driving_time += actual_drive_time
                new_node.arrival_time = current_time

                # HOS driving limit check
                if accumulated_driving_time > vehicle.hos.max_driving_minutes:
                    return False, f"HOS Driving Violation on vehicle {vehicle.id} (Driving {accumulated_driving_time:.1f}m > Max {vehicle.hos.max_driving_minutes}m)", [], 0.0, 0.0

            if node.order:
                order = node.order
                accumulated_weight += order.weight_kg
                accumulated_volume += order.volume_m3

                # Capacity Checks
                if accumulated_weight > vehicle.max_weight_kg:
                    return False, f"Weight capacity exceeded ({accumulated_weight}kg / {vehicle.max_weight_kg}kg)", [], 0.0, 0.0
                if accumulated_volume > vehicle.max_volume_m3:
                    return False, f"Volume capacity exceeded ({accumulated_volume}m3 / {vehicle.max_volume_m3}m3)", [], 0.0, 0.0

                # Service Window Checks
                if current_time < order.earliest_time:
                    current_time = order.earliest_time  # Early arrival: wait for customer window to open

                if current_time > order.latest_time:
                    delay_msg = f"due to {new_node.traffic_condition.value} traffic (+{new_node.traffic_delay_min:.1f}m delay)" if new_node.traffic_delay_min > 0 else ""
                    return False, f"Time window missed for Order {order.id} (Arrived {current_time:.1f}m, Max {order.latest_time}m {delay_msg})", [], 0.0, 0.0

                # Service duration (unloading)
                current_time += order.service_duration

            new_node.departure_time = current_time
            updated_nodes.append(new_node)

        # HOS overall shift limit check
        if (current_time + vehicle.hos.current_shift_minutes) > vehicle.hos.max_shift_minutes:
            return False, f"HOS Shift limit exceeded for driver in vehicle {vehicle.id} ({current_time:.1f}m > Max {vehicle.hos.max_shift_minutes}m)", [], 0.0, 0.0

        return True, "VALID", updated_nodes, total_distance, total_delay


# =====================================================================
# 5. MULTI-DEPOT ROUTING & REBALANCING OPTIMIZER
# =====================================================================

class MultiDepotFleetOptimizer:
    """Dynamic Insertion and Heuristic Solver for Multi-Depot Traffic-Aware Dynamic VRP."""

    def __init__(
        self,
        depots: Dict[str, Depot],
        vehicles: Dict[str, Vehicle],
        traffic_engine: Optional[TrafficEngine] = None
    ):
        self.depots = depots
        self.vehicles = vehicles
        self.traffic_engine = traffic_engine or TrafficEngine()
        self.routes: Dict[str, Route] = {}
        self._initialize_routes()

    def _initialize_routes(self):
        for v_id, vehicle in self.vehicles.items():
            depot = self.depots[vehicle.current_depot_id]
            start_node = RouteNode(
                order=None, depot_id=depot.id, location=depot.location,
                arrival_time=0.0, departure_time=0.0
            )
            end_node = RouteNode(
                order=None, depot_id=depot.id, location=depot.location,
                arrival_time=0.0, departure_time=0.0
            )
            self.routes[v_id] = Route(
                vehicle_id=v_id,
                origin_depot_id=depot.id,
                destination_depot_id=depot.id,
                nodes=[start_node, end_node],
                total_distance_km=0.0,
                total_cost=0.0,
                total_traffic_delay_min=0.0
            )

    def calculate_route_cost(self, route: Route, vehicle: Vehicle) -> Tuple[float, float]:
        """Calculates distance cost, traffic delay penalty, + inter-depot rebalancing penalty."""
        total_dist = 0.0
        for i in range(len(route.nodes) - 1):
            total_dist += route.nodes[i].location.distance_to(route.nodes[i + 1].location)

        base_cost = total_dist * vehicle.cost_per_km
        traffic_penalty = route.total_traffic_delay_min * 0.50  # Cost per minute of traffic delay

        # Rebalancing cost if ending at a foreign depot
        dest_depot_id = route.nodes[-1].depot_id
        rebalance_cost = 0.0
        if dest_depot_id and dest_depot_id != vehicle.home_depot_id:
            dest_depot = self.depots[dest_depot_id]
            home_depot = self.depots[vehicle.home_depot_id]
            rebalance_dist = dest_depot.location.distance_to(home_depot.location)
            rebalance_cost = rebalance_dist * dest_depot.rebalance_penalty_per_km

        return base_cost + traffic_penalty + rebalance_cost, total_dist

    def insert_order_dynamic(self, order: Order) -> Tuple[bool, str]:
        """Dynamically inserts order into the optimal vehicle route with minimum marginal cost."""
        best_cost_delta = float('inf')
        best_candidate: Optional[Tuple[str, Route]] = None
        rejection_reasons = []

        for v_id, route in self.routes.items():
            vehicle = self.vehicles[v_id]

            for idx in range(1, len(route.nodes)):
                candidate_nodes = (
                    route.nodes[:idx] +
                    [RouteNode(order=order, depot_id=None, location=order.location)] +
                    route.nodes[idx:]
                )
                temp_route = Route(
                    vehicle_id=v_id,
                    origin_depot_id=route.origin_depot_id,
                    destination_depot_id=route.destination_depot_id,
                    nodes=candidate_nodes
                )

                valid, msg, scheduled_nodes, dist_km, delay_min = ConstraintChecker.validate_and_compute_schedule(
                    temp_route, vehicle, self.depots, self.traffic_engine
                )

                if valid:
                    temp_route.nodes = scheduled_nodes
                    temp_route.total_distance_km = dist_km
                    temp_route.total_traffic_delay_min = delay_min
                    cost_after, _ = self.calculate_route_cost(temp_route, vehicle)
                    cost_delta = cost_after - route.total_cost

                    if cost_delta < best_cost_delta:
                        best_cost_delta = cost_delta
                        temp_route.total_cost = cost_after
                        best_candidate = (v_id, temp_route)
                else:
                    rejection_reasons.append(f"V[{v_id}]: {msg}")

        if best_candidate:
            v_id, new_route = best_candidate
            self.routes[v_id] = new_route
            return True, f"Allocated to Vehicle {v_id} (Cost Delta +${best_cost_delta:.2f})"

        return False, f"Unable to allocate order within constraints: {'; '.join(rejection_reasons[:2])}"

    def handle_mass_injection(self, orders: List[Order]) -> Dict[str, Tuple[bool, str]]:
        """Handles high-throughput order spikes by processing priority batch queues."""
        results = {}
        # Order by strictest time-windows first
        sorted_orders = sorted(orders, key=lambda x: (x.latest_time - x.earliest_time))
        for order in sorted_orders:
            success, msg = self.insert_order_dynamic(order)
            results[order.id] = (success, msg)
        return results

    def recompute_all_schedules(self) -> Dict[str, Tuple[bool, str]]:
        """Re-evaluates active routes against latest traffic and updates ETAs or flags delays."""
        results = {}
        for v_id, route in self.routes.items():
            vehicle = self.vehicles[v_id]
            valid, msg, scheduled_nodes, dist_km, delay_min = ConstraintChecker.validate_and_compute_schedule(
                route, vehicle, self.depots, self.traffic_engine
            )
            if valid:
                route.nodes = scheduled_nodes
                route.total_distance_km = dist_km
                route.total_traffic_delay_min = delay_min
                route.total_cost, _ = self.calculate_route_cost(route, vehicle)
                results[v_id] = (True, "Schedule updated with current traffic")
            else:
                results[v_id] = (False, f"TRAFFIC CONFLICT: {msg}")
        return results


# =====================================================================
# 6. PRODUCTION-READY TESTING & AUDITING FRAMEWORK
# =====================================================================

class OptimizationAuditor:
    """Evaluates optimization metrics, cost savings, and constraint metrics."""

    @staticmethod
    def audit_system(optimizer: MultiDepotFleetOptimizer) -> Dict[str, any]:
        total_distance = 0.0
        total_cost = 0.0
        total_delay = 0.0
        total_orders_serviced = 0
        violations = 0
        routes_summary = []

        for v_id, route in optimizer.routes.items():
            vehicle = optimizer.vehicles[v_id]
            valid, msg, _, dist, delay = ConstraintChecker.validate_and_compute_schedule(
                route, vehicle, optimizer.depots, optimizer.traffic_engine
            )
            if not valid:
                violations += 1

            total_distance += dist
            total_cost += route.total_cost
            total_delay += delay
            order_count = sum(1 for n in route.nodes if n.order is not None)
            total_orders_serviced += order_count

            routes_summary.append({
                "vehicle_id": v_id,
                "stops": len(route.nodes),
                "orders": order_count,
                "distance_km": round(dist, 2),
                "cost_usd": round(route.total_cost, 2),
                "traffic_delay_min": round(delay, 2),
                "status": "VALID" if valid else f"VIOLATION: {msg}"
            })

        return {
            "total_distance_km": round(total_distance, 2),
            "total_operational_cost": round(total_cost, 2),
            "total_traffic_delay_min": round(total_delay, 2),
            "orders_assigned": total_orders_serviced,
            "constraint_violations": violations,
            "avg_cost_per_order": round(total_cost / max(1, total_orders_serviced), 2),
            "routes_summary": routes_summary
        }

    @staticmethod
    def export_state_json(optimizer: MultiDepotFleetOptimizer, traffic_engine: TrafficEngine, output_file: str):
        """Exports fleet, depots, routes, and active traffic state to JSON for frontend visualization."""
        data = {
            "depots": {k: {"id": v.id, "name": v.name, "lat": v.location.lat, "lon": v.location.lon} for k, v in optimizer.depots.items()},
            "vehicles": {
                k: {
                    "id": v.id,
                    "name": v.name,
                    "home_depot_id": v.home_depot_id,
                    "current_location": {"lat": v.current_location.lat, "lon": v.current_location.lon},
                    "max_weight_kg": v.max_weight_kg,
                    "max_volume_m3": v.max_volume_m3,
                    "cost_per_km": v.cost_per_km,
                    "status": v.status.value
                } for k, v in optimizer.vehicles.items()
            },
            "traffic_incidents": [
                {
                    "id": inc.id,
                    "description": inc.description,
                    "center": {"lat": inc.center.lat, "lon": inc.center.lon},
                    "radius_km": inc.radius_km,
                    "severity": inc.severity.value,
                    "duration_minutes": inc.duration_minutes
                } for inc in traffic_engine.active_incidents.values()
            ],
            "routes": {}
        }

        for v_id, r in optimizer.routes.items():
            data["routes"][v_id] = {
                "vehicle_id": r.vehicle_id,
                "origin_depot_id": r.origin_depot_id,
                "destination_depot_id": r.destination_depot_id,
                "total_distance_km": round(r.total_distance_km, 2),
                "total_cost": round(r.total_cost, 2),
                "total_traffic_delay_min": round(r.total_traffic_delay_min, 2),
                "nodes": [
                    {
                        "type": "ORDER" if n.order else "DEPOT",
                        "id": n.order.id if n.order else n.depot_id,
                        "customer": n.order.customer_name if n.order else "Depot Facility",
                        "lat": n.location.lat,
                        "lon": n.location.lon,
                        "arrival_time": round(n.arrival_time, 1),
                        "departure_time": round(n.departure_time, 1),
                        "traffic_condition": n.traffic_condition.value,
                        "traffic_delay_min": round(n.traffic_delay_min, 1)
                    } for n in r.nodes
                ]
            }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


# =====================================================================
# 7. SIMULATION RUNTIME & DEMONSTRATION
# =====================================================================

if __name__ == "__main__":
    print("==================================================================")
    print(" REAL-TIME MULTI-DEPOT FLEET OPTIMIZER WITH GPS & LIVE TRAFFIC ")
    print("==================================================================\n")

    # 1. Setup Depots (SF Bay Area Logistics Hubs)
    depots = {
        "D1": Depot(id="D1", name="San Francisco Hub", location=Location(37.7749, -122.4194)),
        "D2": Depot(id="D2", name="San Jose Fulfillment Center", location=Location(37.3382, -121.8863)),
        "D3": Depot(id="D3", name="Oakland East Bay Port", location=Location(37.8044, -122.2712))
    }

    # 2. Setup Fleet Vehicles (Notice corrected current_location parameter)
    vehicles = {
        "V1": Vehicle(
            id="V1", name="EcoVan SF-Express", home_depot_id="D1", current_depot_id="D1",
            current_location=depots["D1"].location, max_weight_kg=1200, max_volume_m3=12,
            cost_per_km=1.80, hos=DriverHOS()
        ),
        "V2": Vehicle(
            id="V2", name="FreightHauler SJ-Prime", home_depot_id="D2", current_depot_id="D2",
            current_location=depots["D2"].location, max_weight_kg=2200, max_volume_m3=20,
            cost_per_km=2.40, hos=DriverHOS()
        ),
        "V3": Vehicle(
            id="V3", name="RapidVan Oakland-Metro", home_depot_id="D3", current_depot_id="D3",
            current_location=depots["D3"].location, max_weight_kg=1500, max_volume_m3=15,
            cost_per_km=2.10, hos=DriverHOS()
        )
    }

    # 3. Initialize Engines
    traffic_engine = TrafficEngine(base_highway_speed=65.0, base_city_speed=40.0)
    telemetry = TelemetryIngestor(max_speed_kmh=130.0)
    optimizer = MultiDepotFleetOptimizer(depots, vehicles, traffic_engine)

    # 4. GPS Telemetry & Adversarial Teleportation Tests
    print("--- 1. RUNNING GPS TELEMETRY & ANTI-SPOOFING TESTS ---")
    t0 = time.time()

    # Normal valid GPS ping
    ping1 = GPSPing("V1", Location(37.7749, -122.4194), timestamp=t0, speed_kmh=0.0)
    accepted1, msg1 = telemetry.process_ping(ping1)
    print(f"Ping 1 (Initial V1 Depot Check-in): {msg1}")

    # Valid moving ping 10 minutes later (7.5 km down US-101 at 45 km/h)
    ping2 = GPSPing("V1", Location(37.7120, -122.4010), timestamp=t0 + 600, speed_kmh=45.0)
    accepted2, msg2 = telemetry.process_ping(ping2)
    print(f"Ping 2 (Valid En-route GPS Breadcrumb): {msg2}")

    # Adversarial GPS Spoofing Attack: claims to jump to Los Angeles (~550km away) in 15 seconds!
    spoofed_ping = GPSPing("V1", Location(34.0522, -118.2437), timestamp=t0 + 615, speed_kmh=90.0)
    accepted_spoof, msg_spoof = telemetry.process_ping(spoofed_ping)
    print(f"Ping 3 (Adversarial GPS Spoofing Attack): {msg_spoof}\n")

    # 5. Ingest Dynamic Customer Delivery Orders
    print("--- 2. INGESTING REAL-TIME CUSTOMER ORDERS ---")
    orders = [
        Order("O1", "SFO Cargo Terminal", Location(37.6213, -122.3790), weight_kg=250, volume_m3=2.2, earliest_time=15, latest_time=90, service_duration=15),
        Order("O2", "San Mateo Medical Center", Location(37.5485, -122.3186), weight_kg=380, volume_m3=3.0, earliest_time=25, latest_time=140, service_duration=20),
        Order("O3", "Stanford Biotech Palo Alto", Location(37.4419, -122.1430), weight_kg=290, volume_m3=2.5, earliest_time=35, latest_time=180, service_duration=15),
        Order("O4", "Mountain View Tech Campus", Location(37.3861, -122.0839), weight_kg=450, volume_m3=4.0, earliest_time=20, latest_time=120, service_duration=20),
        Order("O5", "Berkeley Distribution Center", Location(37.8715, -122.2730), weight_kg=320, volume_m3=2.8, earliest_time=10, latest_time=100, service_duration=15),
    ]

    allocation_results = optimizer.handle_mass_injection(orders)
    for oid, (success, reason) in allocation_results.items():
        print(f" -> Order {oid}: {'[SUCCESS]' if success else '[REJECTED]'} {reason}")

    # 6. Initial Audit Baseline
    print("\n--- 3. BASELINE FLEET AUDIT METRICS (CLEAR TRAFFIC) ---")
    baseline_metrics = OptimizationAuditor.audit_system(optimizer)
    print(f"Total Distance: {baseline_metrics['total_distance_km']} km")
    print(f"Total Operating Cost: ${baseline_metrics['total_operational_cost']}")
    print(f"Orders Assigned: {baseline_metrics['orders_assigned']}")
    print(f"Traffic Delay Added: {baseline_metrics['total_traffic_delay_min']} minutes")

    # 7. Inject Sudden Real-Time Traffic Congestion
    print("\n--- 4. INJECTING REAL-TIME TRAFFIC CONGESTION & INCIDENT ---")
    incident = TrafficIncident(
        id="INC-101-SANMATEO",
        description="Multi-vehicle collision and lane blockage on US-101 South at San Mateo",
        center=Location(37.5485, -122.3186),
        radius_km=12.0,
        severity=TrafficSeverity.HEAVY,
        start_time=0.0,
        duration_minutes=180.0
    )
    traffic_engine.report_incident(incident)
    print(f"[TRAFFIC ALERT] {incident.description} -> SEVERITY: {incident.severity.value} (-55% speed, +120% delay)")

    # 8. Re-evaluate Active Routes with Traffic Delay
    print("\n--- 5. TRAFFIC-AWARE ETA RECALCULATION & DISPATCH AUDIT ---")
    reschedule_status = optimizer.recompute_all_schedules()
    for v_id, (ok, note) in reschedule_status.items():
        print(f"Vehicle {v_id}: {'[FEASIBLE]' if ok else '[DELAY WARNING]'} {note}")

    post_traffic_metrics = OptimizationAuditor.audit_system(optimizer)
    print(f"\nUpdated Distance: {post_traffic_metrics['total_distance_km']} km")
    print(f"Updated Cost (with Traffic Penalty): ${post_traffic_metrics['total_operational_cost']}")
    print(f"Traffic Delay Incurred: {post_traffic_metrics['total_traffic_delay_min']} minutes across fleet")

    # 9. Export State for Visual Dashboard
    OptimizationAuditor.export_state_json(optimizer, traffic_engine, "fleet_state.json")
    print("\n[SUCCESS] Fleet state and traffic data exported to 'fleet_state.json' for interactive dashboard visualization.")
    print("==================================================================")
