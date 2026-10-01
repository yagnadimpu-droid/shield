"""
SmartFleet - Real-Time Multi-Depot Fleet Optimization Backend Server
===================================================================
Flask REST API server integrating:
- Google OR-Tools Multi-Depot VRPTW Solver & Sub-150ms Heuristic Engine
- SQLite & JSON Data Persistence Layer
- Dynamic Event Pipeline Orchestrator (Orders, Telemetry, Traffic, Breakdowns)
- Adversarial Safeguards (Anti-Spoofing, Network Blackout, Breakdown Redistribution)
"""

import os
import sys
import time
import json
import sqlite3
from typing import Dict, Any, List, Optional
from flask import Flask, request, jsonify, send_from_directory, render_template

from optimizer_core import (
    SmartFleetOrchestrator,
    Location,
    GPSPing,
    Order,
    VehicleStatus,
    TrafficSeverity
)

# App Configuration
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "smartfleet.db")
JSON_STATE_PATH = os.path.join(APP_DIR, "fleet_state.json")

app = Flask(__name__, static_folder=APP_DIR, static_url_path="")

# =====================================================================
# SQLITE DATA LAYER
# =====================================================================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite schema for depots, vehicles, orders, telemetry, and events."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS depots (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                zone_label TEXT NOT NULL,
                rebalance_penalty_per_km REAL NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                home_depot_id TEXT NOT NULL,
                current_depot_id TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                max_weight_kg REAL NOT NULL,
                max_volume_m3 REAL NOT NULL,
                cost_per_km REAL NOT NULL,
                fuel_cost_per_km REAL NOT NULL,
                status TEXT NOT NULL,
                telemetry_locked INTEGER NOT NULL DEFAULT 0,
                color_hex TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                customer_name TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                weight_kg REAL NOT NULL,
                volume_m3 REAL NOT NULL,
                earliest_time REAL NOT NULL,
                latest_time REAL NOT NULL,
                service_duration REAL NOT NULL,
                is_cancelled INTEGER NOT NULL DEFAULT 0,
                assigned_vehicle_id TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                vehicle_id TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                speed_kmh REAL NOT NULL,
                is_spoofed INTEGER NOT NULL DEFAULT 0,
                status_note TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                level TEXT NOT NULL,
                latency_ms REAL NOT NULL
            );
        """)
        conn.commit()

def sync_state_to_db(orchestrator: SmartFleetOrchestrator):
    """Synchronizes current in-memory orchestrator state to SQLite & JSON state store."""
    state = orchestrator.get_full_state()
    
    # 1. Write JSON state
    try:
        with open(JSON_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"[DB] Error writing fleet_state.json: {e}")

    # 2. Sync to SQLite
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Upsert Depots
            for d in state["depots"].values():
                cursor.execute("""
                    INSERT INTO depots (id, name, lat, lon, zone_label, rebalance_penalty_per_km)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name=excluded.name, lat=excluded.lat, lon=excluded.lon,
                        zone_label=excluded.zone_label, rebalance_penalty_per_km=excluded.rebalance_penalty_per_km;
                """, (d["id"], d["name"], d["lat"], d["lon"], d["zone_label"], d["rebalance_penalty_per_km"]))
                
            # Upsert Vehicles
            for v in state["vehicles"].values():
                cursor.execute("""
                    INSERT INTO vehicles (id, name, home_depot_id, current_depot_id, lat, lon,
                                         max_weight_kg, max_volume_m3, cost_per_km, fuel_cost_per_km,
                                         status, telemetry_locked, color_hex)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        home_depot_id=excluded.home_depot_id, current_depot_id=excluded.current_depot_id,
                        lat=excluded.lat, lon=excluded.lon, max_weight_kg=excluded.max_weight_kg,
                        max_volume_m3=excluded.max_volume_m3, cost_per_km=excluded.cost_per_km,
                        fuel_cost_per_km=excluded.fuel_cost_per_km, status=excluded.status,
                        telemetry_locked=excluded.telemetry_locked, color_hex=excluded.color_hex;
                """, (v["id"], v["name"], v["home_depot_id"], v["current_depot_id"], v["lat"], v["lon"],
                      v["max_weight_kg"], v["max_volume_m3"], v["cost_per_km"], v["fuel_cost_per_km"],
                      v["status"], 1 if v["telemetry_locked"] else 0, v["color_hex"]))
                
            # Upsert Orders
            for o in state["orders"].values():
                cursor.execute("""
                    INSERT INTO orders (id, customer_name, lat, lon, weight_kg, volume_m3,
                                       earliest_time, latest_time, service_duration, is_cancelled, assigned_vehicle_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        customer_name=excluded.customer_name, lat=excluded.lat, lon=excluded.lon,
                        weight_kg=excluded.weight_kg, volume_m3=excluded.volume_m3,
                        earliest_time=excluded.earliest_time, latest_time=excluded.latest_time,
                        service_duration=excluded.service_duration, is_cancelled=excluded.is_cancelled,
                        assigned_vehicle_id=excluded.assigned_vehicle_id;
                """, (o["id"], o["customer_name"], o["lat"], o["lon"], o["weight_kg"], o["volume_m3"],
                      o["earliest_time"], o["latest_time"], o["service_duration"],
                      1 if o["is_cancelled"] else 0, o["assigned_vehicle_id"]))
                
            conn.commit()
    except Exception as e:
        print(f"[DB] Error syncing to SQLite: {e}")

# Global Engine Instance
orchestrator = SmartFleetOrchestrator()
init_db()
sync_state_to_db(orchestrator)


# =====================================================================
# STATIC / SPA ROUTES
# =====================================================================

@app.route("/")
def index():
    return send_from_directory(APP_DIR, "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(APP_DIR, path)


# =====================================================================
# REST API ENDPOINTS
# =====================================================================

@app.route("/api/state", methods=["GET"])
def get_state():
    """Returns the full fleet telemetry, depots, orders, routes, KPIs and logs."""
    state = orchestrator.get_full_state()
    return jsonify(state)


@app.route("/api/initialize", methods=["POST"])
def initialize_fleet():
    """Initializes/resets the 3 depots (A, B, C), vehicles, and baseline orders."""
    orchestrator.initialize_default_state()
    sync_state_to_db(orchestrator)
    return jsonify({
        "status": "SUCCESS",
        "message": "Initialized 3 Depots, 4 Fleet Vehicles, and baseline orders.",
        "state": orchestrator.get_full_state()
    })


@app.route("/api/optimize", methods=["POST"])
def run_optimization():
    """Triggers the full multi-depot VRPTW constraint gate and solver pipeline (<150ms)."""
    result = orchestrator.run_pipeline("MANUAL_OPTIMIZE", "User requested dynamic route re-optimization")
    sync_state_to_db(orchestrator)
    return jsonify({
        "result": result,
        "state": orchestrator.get_full_state()
    })


@app.route("/api/inject-order-surge", methods=["POST"])
def inject_order_surge():
    """Simulates a sudden surge influx of dynamic customer orders with weights & time windows."""
    count = request.json.get("count", 5) if request.is_json else 5
    result = orchestrator.handle_inject_orders_surge(count=count)
    sync_state_to_db(orchestrator)
    return jsonify({
        "result": result,
        "state": orchestrator.get_full_state()
    })


@app.route("/api/breakdown", methods=["POST"])
def trigger_breakdown():
    """Ejects a vehicle from the active pool and redistributes orders to compliant drivers."""
    req_data = request.get_json(silent=True) or {}
    vehicle_id = req_data.get("vehicle_id", "V2")
    result = orchestrator.handle_vehicle_breakdown(vehicle_id=vehicle_id)
    sync_state_to_db(orchestrator)
    return jsonify({
        "result": result,
        "state": orchestrator.get_full_state()
    })


@app.route("/api/gps-spoof", methods=["POST"])
def simulate_gps_spoof():
    """Simulates illegal velocity jump / spoofing attack and locks vehicle feed."""
    req_data = request.get_json(silent=True) or {}
    vehicle_id = req_data.get("vehicle_id", "V1")
    result = orchestrator.handle_gps_spoof(vehicle_id=vehicle_id)
    sync_state_to_db(orchestrator)
    return jsonify({
        "result": result,
        "state": orchestrator.get_full_state()
    })


@app.route("/api/gps-ping", methods=["POST"])
def ingest_gps_ping():
    """Live ingestion of real-time GPS coordinates with anti-spoofing check."""
    data = request.get_json(silent=True) or {}
    v_id = data.get("vehicle_id", "V1")
    lat = float(data.get("lat", 37.7749))
    lon = float(data.get("lon", -122.4194))
    speed = float(data.get("speed_kmh", 45.0))
    ts = float(data.get("timestamp", time.time()))

    ping = GPSPing(
        vehicle_id=v_id,
        location=Location(lat, lon),
        timestamp=ts,
        speed_kmh=speed
    )

    accepted, reason = orchestrator.telemetry_security.process_ping(ping)

    if accepted and v_id in orchestrator.vehicles:
        veh = orchestrator.vehicles[v_id]
        if not orchestrator.network_blackout_mode and not veh.telemetry_locked:
            veh.current_location = ping.location
            veh.last_valid_location = ping.location

    # Log to SQLite telemetry audit
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO telemetry_audit (timestamp, vehicle_id, lat, lon, speed_kmh, is_spoofed, status_note)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (ts, v_id, lat, lon, speed, 0 if accepted else 1, reason))
            conn.commit()
    except Exception as e:
        print(f"[DB] Error logging telemetry: {e}")

    return jsonify({
        "accepted": accepted,
        "reason": reason,
        "state": orchestrator.get_full_state()
    })


@app.route("/api/toggle-blackout", methods=["POST"])
def toggle_blackout():
    """Toggles Network Blackout Mode (freezes coordinates, blocks unsafe reassignments)."""
    result = orchestrator.handle_toggle_blackout()
    sync_state_to_db(orchestrator)
    return jsonify({
        "result": result,
        "state": orchestrator.get_full_state()
    })


@app.route("/api/mass-cancellation", methods=["POST"])
def mass_cancellation():
    """Prunes cancelled order stops from active routes and recalculates shortest paths."""
    req_data = request.get_json(silent=True) or {}
    order_ids = req_data.get("order_ids", None)
    result = orchestrator.handle_mass_cancellation(order_ids=order_ids)
    sync_state_to_db(orchestrator)
    return jsonify({
        "result": result,
        "state": orchestrator.get_full_state()
    })


@app.route("/api/cross-depot-rebalance", methods=["POST"])
def cross_depot_rebalance():
    """Evaluates cost-aware inter-depot vehicle transfer (transfer cost vs delay penalty)."""
    result = orchestrator.handle_cost_aware_rebalance()
    sync_state_to_db(orchestrator)
    return jsonify({
        "result": result,
        "state": orchestrator.get_full_state()
    })


@app.route("/api/traffic-surge", methods=["POST"])
def traffic_surge():
    """Injects or clears traffic congestion jump on the corridor."""
    req_data = request.get_json(silent=True) or {}
    severity = req_data.get("severity", "HEAVY")
    if severity.upper() == "CLEAR":
        orchestrator.traffic_engine.active_incidents.clear()
        orchestrator.log_event("TRAFFIC_CLEAR", "Traffic cleared on all corridors. Normal speed restored.", "INFO")
        result = orchestrator.run_pipeline("TRAFFIC_CLEAR", "Routes updated to free-flow travel speeds")
    else:
        result = orchestrator.handle_traffic_surge(severity=severity)

    sync_state_to_db(orchestrator)
    return jsonify({
        "result": result,
        "state": orchestrator.get_full_state()
    })


@app.route("/api/add-order", methods=["POST"])
def add_custom_order():
    """Allows injecting custom bookings dynamically."""
    data = request.get_json(silent=True) or {}
    oid = f"ORD-{int(time.time()) % 10000}"
    name = data.get("customer_name", f"Order {oid}")
    lat = float(data.get("lat", 37.5 + (time.time() % 10) * 0.02))
    lon = float(data.get("lon", -122.2 - (time.time() % 10) * 0.02))
    weight = float(data.get("weight_kg", 250.0))
    volume = float(data.get("volume_m3", 2.0))
    start_tw = float(data.get("earliest_time", 10.0))
    end_tw = float(data.get("latest_time", 90.0))

    new_ord = Order(
        id=oid,
        customer_name=name,
        location=Location(lat, lon),
        weight_kg=weight,
        volume_m3=volume,
        earliest_time=start_tw,
        latest_time=end_tw,
        service_duration=15.0
    )
    orchestrator.orders[oid] = new_ord
    result = orchestrator.run_pipeline("NEW_BOOKING_INGESTED", f"Dynamic booking {oid} received and routed")
    sync_state_to_db(orchestrator)

    return jsonify({
        "result": result,
        "order": {
            "id": oid,
            "customer_name": name,
            "lat": lat,
            "lon": lon,
            "weight_kg": weight,
            "volume_m3": volume
        },
        "state": orchestrator.get_full_state()
    })


@app.route("/api/audit-logs", methods=["GET"])
def get_audit_logs():
    """Returns recent telemetry audit logs from SQLite."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM telemetry_audit ORDER BY id DESC LIMIT 50;")
            rows = [dict(r) for r in cursor.fetchall()]
            return jsonify({"status": "SUCCESS", "logs": rows})
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e), "logs": []})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"================================================================")
    print(f"SmartFleet: Multi-Depot Fleet Optimization Engine Backend")
    print(f"Listening on http://localhost:{port}")
    print(f"================================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
