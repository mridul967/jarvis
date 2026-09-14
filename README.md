# Quantum-Inspired Intelligent Traffic Route Optimization

**AICTE Smart India Hackathon (SIH) 2026 — Quantum Technology Vertical**  
**Organization:** Egreen Quanta  
**Problem Statement ID:** SIH26137  
**Problem Title:** Quantum-Inspired Intelligent Traffic Route Optimization in Transportation Systems Using Metaheuristic Optimization

---

## Overview

Modern urban transportation systems face major challenges such as traffic congestion, inefficient route planning, high fuel consumption, and increased operational costs. Classical optimization methods often struggle with large-scale Vehicle Routing Problems (VRP) and dynamic shortest-path problems due to their NP-hard nature and rapidly changing traffic conditions.

This repository implements a **Quantum-Inspired Metaheuristic Optimization Framework** for intelligent traffic route optimization. The framework models the transportation network as a weighted graph and uses quantum-inspired algorithms to generate near-optimal vehicle routes under real-time or simulated traffic conditions.

The core intelligent model encapsulates three optimization algorithms:

- **QACO** — Dynamic Interference-Tunneling Quantum-Inspired Ant Colony Optimization
- **QPSO** — Quantum-inspired Particle Swarm Optimization
- **SBM** — Search-Based Metaheuristic module

These algorithms are wrapped inside a unified model interface to support experimentation, benchmarking, dynamic traffic adaptation, and route visualization.

---

## Problem Statement

The objective of this project is to develop a quantum-inspired optimization platform that can dynamically generate efficient vehicle routes in a transportation network.

The transportation network is represented as a weighted graph where nodes represent intersections, depots, or customer locations, and edges represent road segments with weights based on travel time, distance, congestion, or other traffic-related costs.

The framework aims to solve:

- Large-scale Vehicle Routing Problems (VRP)
- Dynamic shortest-path problems
- Congestion-aware route optimization
- Multi-objective transportation routing problems

The proposed system is benchmarked against classical metaheuristic algorithms and exact or heuristic shortest-path methods.

---

## Objectives

This project focuses on the following objectives:

1. Design a quantum-inspired metaheuristic framework for solving large-scale VRP and shortest-path problems.
2. Minimize total travel time, total distance, and traffic congestion.
3. Reduce computational complexity while improving convergence speed and solution quality compared with classical algorithms.
4. Demonstrate scalability for smart-city logistics and intelligent transportation systems.
5. Provide a reusable software package that encapsulates multiple quantum-inspired optimization algorithms under a common interface.

---

## Key Features

- Graph-based modeling of transportation networks
- Dynamic edge weight updates based on traffic conditions
- Quantum-inspired optimization algorithms
- Unified model encapsulation for QACO, QPSO, and SBM
- Constraint handling for capacity, time windows, and route feasibility
- Route encoding and decoding mechanisms for discrete routing problems
- Convergence analysis and fitness tracking
- Benchmarking against classical metaheuristics
- Visualization of optimized routes on graphs or maps
- Modular and extensible repository structure
- Suitable for real-time or simulated traffic scenarios

---

## Algorithms Implemented

This repository implements a multi-algorithm optimization suite. Each algorithm can be used independently or as part of a combined experimental pipeline.

| Algorithm | Full Form | Role |
|---|---|---|
| QACO | Dynamic Interference-Tunneling Quantum-Inspired Ant Colony Optimization | Probabilistic route construction using quantum interference and tunneling for dynamic traffic adaptation |
| QPSO | Quantum-inspired Particle Swarm Optimization | Swarm-based search using quantum potential well and probabilistic particle updates |
| SBM | Search-Based Metaheuristic | Complementary metaheuristic module for local refinement, comparison, or hybrid search |

---

## QACO: Dynamic Interference-Tunneling Quantum-Inspired Ant Colony Optimization

QACO is not just a simple probabilistic wrapper; it is a dynamic framework designed specifically for real-time traffic adaptation. It uses the interference between historical pheromone information and real-time traffic states, combined with tunneling-inspired non-local perturbations for adaptive recovery from traffic-induced local optima.

### Key Quantum Concepts Used

- Quantum Interference (Amplitude-based route selection)
- Quantum Tunneling (Non-local stagnation recovery)
- Adaptive Traffic-Volatility Control

### Working Principle

**Quantum Interference for Global Search and Dynamic Adaptation**
Classical Ant Colony Optimization relies heavily on historical pheromones, which can cause the algorithm to stubbornly prefer routes that were good in the past but are currently jammed. QACO solves this by representing route preferences as quantum-inspired amplitudes, which incorporate both magnitude and phase, rather than simple probabilities. 

When historical pheromone data meets real-time traffic data, these amplitudes interfere with each other. If both historical data and current traffic indicate a good route, they constructively interfere, highly amplifying the selection probability. Conversely, if the historical data suggests a good route but the current traffic is terrible, they destructively interfere, causing the probability to collapse immediately. This allows the algorithm to adapt instantly to dynamic traffic shocks without waiting for slow pheromone evaporation, ensuring a much stronger and more responsive global search.

**Quantum Tunneling for Faster Convergence and Escaping Local Optima**
When the search stagnates, or when a sudden traffic shock renders the current best routes obsolete, classical algorithms waste countless iterations trying to climb out of the local optimum using small steps. QACO employs a quantum-tunneling-inspired non-local perturbation. Instead of making small, incremental local search modifications, it triggers a disruptive, large-scale route change—such as a massive segment reversal or cross-route relocation. This allows the search to effectively "tunnel" through the fitness barrier into a completely new, promising region of the search space, drastically reducing wasted iterations and accelerating convergence.

**Adaptive Exploration vs. Exploitation**
The balance between exploration and exploitation is governed by an adaptive controller that continuously monitors traffic volatility and search stagnation. In stable traffic conditions, the algorithm exploits the best-known routes. However, when sudden traffic changes occur, the interference patterns shift, and the probability of triggering a tunneling event increases. This forces the algorithm to immediately abandon outdated routes and explore new alternatives, maintaining a perfect balance even in highly dynamic environments.

### Layered Architecture

The QACO framework operates through a structured, multi-layered pipeline:

1. **Dynamic Transportation Graph**: Models the network with real-time travel time and congestion weights.
2. **Quantum Amplitude Representation**: Assigns complex-inspired amplitudes to every candidate edge.
3. **Quantum Interference**: Combines historical pheromones with real-time traffic and heuristic data to compute final selection probabilities.
4. **Ant Route Construction**: Artificial ants sample routes based on the interfered probabilities while respecting capacity and time-window constraints.
5. **Local Search Refinement**: Applies standard local improvements to the constructed routes.
6. **Tunneling Mechanism**: Triggers non-local route perturbations if stagnation or high traffic volatility is detected.
7. **Dynamic Update**: Recalculates traffic weights and repeats the loop for continuous real-time adaptation.

---

## QPSO: Quantum-inspired Particle Swarm Optimization

QPSO adapts Particle Swarm Optimization using quantum-behaved search dynamics.

### Key Quantum Concepts Used

- Quantum superposition
- Probability amplitude representation
- Quantum potential well
- Mean best attractor
- Adaptive contraction-expansion coefficient
- Quantum tunneling-inspired escape mechanism

### Working Principle

In classical PSO, particles move using velocity and position updates. In QPSO, particles are treated as quantum particles influenced by an attractive potential formed using:

- Personal best solution, `pbest`
- Global best solution, `gbest`
- Mean best position of the swarm, `mbest`

The position update is probabilistic and helps the swarm explore a larger solution space while converging faster toward promising regions.

For discrete routing problems, QPSO uses route encoding mechanisms such as:

- Priority-based encoding
- Edge probability encoding
- Route decoding and repair
- Local search refinement

QPSO is effective for balancing global exploration and convergence speed.

---

## SBM: Search-Based Metaheuristic

SBM is included as a complementary metaheuristic module. It can be used for:

- Baseline comparison
- Local search refinement
- Hybrid optimization support
- Solution repair
- Additional exploration of routing neighborhoods

Depending on the implementation, SBM may include one or more of the following mechanisms:

- Stochastic search
- Neighborhood-based search
- Greedy repair
- Mutation and perturbation
- Route segment improvement
- Local search heuristics such as 2-opt, Or-opt, swap, relocate, and reverse-segment

SBM helps improve solution quality and can be combined with QACO or QPSO as a hybrid optimizer.

---

## Model Encapsulation

All three algorithms are encapsulated inside a unified intelligent optimization model. This allows users to switch between algorithms, compare performance, or run hybrid pipelines without changing the core problem formulation.

The model exposes a common interface:

```python
optimizer = OptimizerSuite(
    algorithms=["QACO", "QPSO", "SBM"],
    problem=vrp_problem,
    config=experiment_config
)

results = optimizer.optimize()
