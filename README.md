# ⚙️ DoodleForge

> **Real-Time Sketch-to-Physics Generative Creature Sandbox**  
> *Transform freehand sketches of creatures, monsters, and contraptions into rigged 2D physical bodies with joints, motors, and procedural locomotion.*

[![CI](https://github.com/Manansur108/doodleforge/actions/workflows/ci.yml/badge.svg)](https://github.com/Manansur108/doodleforge/actions)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Matter.js](https://img.shields.io/badge/Physics-Matter.js%202D-ff4081.svg)](https://brm.io/matter-js/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests Passing](https://img.shields.io/badge/tests-42%20passed%20%7C%20100%25-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-90%25-success.svg)]()

---

## 🌟 Overview

**DoodleForge** is an interactive browser playground and physics synthesis engine that turns hand-drawn doodle strokes into living, walking, and reacting 2D physical creatures. 

Draw an organic torso and attach limbs, heads, wings, tails, or wheels. DoodleForge parses stroke geometry, detects anatomical parts and pivot attachment points, synthesizes a 2D rigid-body constraint graph with revolute joints and motors, and coordinates locomotion through a biological **Central Pattern Generator (CPG)**.

Creatures inhabit an interactive ecological sandbox featuring dynamic gravity, bounce pads, ramps, and nutrient pellets. Autonomous steering loops (Reynolds Boids) drive hunger and foraging behaviors, allowing user-drawn organisms to interact with each other and their environment.

```
       [ Freehand Sketch ]
                │
                ▼
  ┌─────────────────────────────┐
  │  RDP Stroke Vectorization   │
  │  & Contour Geometry Solver  │
  └─────────────┬───────────────┘
                │
                ▼
  ┌─────────────────────────────┐
  │   Semantic Segmentation     │
  │   Torso / Head / Limbs /    │
  │   Wings / Tail / Wheels     │
  └─────────────┬───────────────┘
                │
                ▼
  ┌─────────────────────────────┐
  │    Physics Auto-Rigging     │
  │  Bodies, Pin Joints, Motors │
  └─────────────┬───────────────┘
                │
                ▼
  ┌─────────────────────────────┐
  │  Locomotion CPG & Sandbox   │
  │  Phase-Coupled Oscillators  │
  │  + Autonomous Steering AI   │
  └─────────────────────────────┘
```

---

## 🔬 Key Architecture & Innovations

### 1. Stroke Vectorization & Geometry Decomposition (`geometry.py`)
- **Ramer-Douglas-Peucker (RDP)** polyline simplification eliminates freehand noise while preserving key anatomical inflection vertices.
- **Arc-Length Resampling** redistributes equidistant control points along complex contours.
- **Second Central Moments of Area**: Evaluates principal orientation axes ($\theta = \frac{1}{2} \operatorname{atan2}(2 \mu_{11}, \mu_{20} - \mu_{02})$) and aspect ratios.
- **Closest-Polyline Contact Finder**: Discovers true Euclidean boundaries to place realistic skeletal pivot joints.

### 2. Anatomical Classification Pipeline (`segmentation.py`)
- **Torso Identification**: Discovers the core body mass based on enclosed area, compactness, and central spatial proximity.
- **Appendage Tagging**: Classifies limbs relative to the torso frame:
  - **Legs**: Downward-oriented limbs; automatically identifies multi-segment knees (femur and tibia segments).
  - **Wings**: High lateral appendages with aerodynamic flapping properties.
  - **Head**: Anterior/sensory structure with stabilizing neck constraint.
  - **Tail**: Posterior counterweight with flexible chain dynamics.
  - **Wheels**: High-compactness circular contours with continuous rotary drive axles.

### 3. Physics Rigging & Constraint Synthesis (`rigging.py`)
- Converts segmented components into `RigidBodyDef`s and `JointDef`s with precise local anchors and angular bounds.
- Generates collision filter masks to prevent self-intersection jams while preserving realistic interactions with the ground and obstacles.

### 4. Central Pattern Generator (CPG) Locomotion (`locomotion.py`)
- Synthesizes coordinated phase-offset oscillations:
  $$\theta_i(t) = \theta_{\text{offset}} + A_i \cdot \sin(2\pi f \cdot t + \phi_i)$$
- Asymmetric stance-and-swing kinematics with real-time **PD motor torque controllers**:
  $$\tau = K_p (\theta_{\text{target}} - \theta_{\text{current}}) - K_d \dot{\theta}$$
- Pre-configured biological gaits: **Bipedal Alternating Stride**, **Quadruped Trot & Gallop**, **Hexapod Tripod Ripple**, **Avian Flapping**, and **Serpentine Traveling Waves**.

### 5. Pure-Python Headless 2D Physics Simulator (`simulator.py`)
- Built-in headless simulation engine featuring semi-implicit Euler integration, position-based joint constraint relaxation, Coulomb ground friction, and stability telemetry.
- Evaluates displacement, velocity, fall probability, and energy efficiency without requiring a browser.

### 6. Evolutionary Gait Optimizer (`optimizer.py`)
- Implements an elitist $(1 + \lambda)$ evolutionary strategy evaluating headless physical trials.
- Optimizes motor frequencies, joint amplitudes, and phase offsets to maximize forward speed and stability.

### 7. Interactive Multi-Creature Sandbox (`app.js` & `steering.py`)
- Real-time client-side simulation powered by **Matter.js** with neon cyberpunk rendering.
- Interactive food dropping: creatures use Reynolds **Seek**, **Wander**, and **Flee** steering loops to locate and consume energy pellets.
- Synthesized audio using the **Web Audio API** (biomechanical footsteps, motor whirrs, food chimes).

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10+
- Modern Web Browser (Chrome, Firefox, Edge, Safari)

### Installation
```bash
git clone https://github.com/Manansur108/doodleforge.git
cd doodleforge
pip install -e ".[dev]"
```

### Launch Interactive Web Sandbox
```bash
doodleforge serve --port 8000
```
Open **`http://127.0.0.1:8000`** in your browser.

---

## 💻 CLI Commands

DoodleForge includes a command-line interface for running headless simulations, listing presets, and executing evolutionary optimizations:

```bash
# List all pre-engineered creatures
doodleforge presets

# Run a headless physics simulation benchmark
doodleforge simulate --preset preset_cyber_cheetah --duration 3.0

# Evolve creature gait parameters using AI
doodleforge optimize --preset preset_bipedal_strider --generations 15

# Launch the FastAPI web server
doodleforge serve --host 127.0.0.1 --port 8000
```

---

## 📡 REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | `GET` | Service status and version check |
| `/api/presets` | `GET` | List all pre-engineered creature blueprints |
| `/api/presets/{preset_id}` | `GET` | Retrieve blueprint for a specific specimen |
| `/api/rig` | `POST` | Vectorize strokes and compile physics blueprint |
| `/api/simulate` | `POST` | Run headless simulation and return displacement/telemetry |
| `/api/optimize-gait` | `POST` | Evolutionary optimization of creature gait |
| `/api/export` | `POST` | Validate and export portable blueprint JSON |
| `/` | `GET` | Interactive browser studio & Matter.js sandbox |

### Example: Auto-Rig Request
```json
POST /api/rig
Content-Type: application/json

{
  "name": "Bionic-Crawler",
  "simplify_tolerance": 2.5,
  "strokes": [
    {
      "points": [{"x": 200, "y": 200}, {"x": 300, "y": 200}, {"x": 300, "y": 250}, {"x": 200, "y": 250}],
      "closed": true,
      "color": "#00e5ff"
    },
    {
      "points": [{"x": 220, "y": 250}, {"x": 220, "y": 320}],
      "closed": false,
      "color": "#00e676"
    },
    {
      "points": [{"x": 280, "y": 250}, {"x": 280, "y": 320}],
      "closed": false,
      "color": "#00e676"
    }
  ]
}
```

---

## 🧬 Built-in Creature Presets

| Specimen | Gait Type | Description |
|---|---|---|
| **Cyber-Cheetah** | `quadruped_trot` | 4 high-traction legs, stabilizing head, and counterweight tail |
| **Bipedal Strider** | `biped_stride` | Tall two-legged walker with alternating $\pi$-phase stride |
| **Hexapod Scuttler** | `hexapod_ripple` | Low-profile 6-legged insect with tripod ripple locomotion |
| **Pterodactyl Flapper** | `avian_flap` | Aerodynamic body with dual motorized aerofoil flapping wings |
| **Wheeled Dune-Rover** | `wheeled_drive` | High-torque motorized vehicle chassis with twin axle drives |

---

## 🧪 Testing & Quality Assurance

DoodleForge comes with a comprehensive test suite covering geometry, anatomical segmentation, constraint rigging, CPG controllers, steering behaviors, headless physics, evolutionary optimization, presets, CLI, and REST endpoints:

```bash
# Run all tests
pytest -v

# Run with coverage report
pytest --cov=doodleforge tests/
```

**Results:**
- **42 tests passing** (100% pass rate)
- **90% code coverage**

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
