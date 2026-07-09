# Backend Documentation

This folder contains backend planning documents for the DICT Program and Event Attendance Monitoring and Reporting System.

## Documents

* [Backend API Plan](backend-api-plan.md) - REST-style API guide based on the current DFD, ERD, permissions matrix, and MySQL schema.
* [FastAPI Stack Decision](fastapi-stack-decision.md) - selected backend stack and frontend-backend hosting approach.
* [FastAPI Backend Scaffold Implementation Plan](../../docs/superpowers/plans/2026-07-09-fastapi-backend-scaffold.md) - step-by-step plan for creating the initial backend project files.

## Current Scope

The selected backend framework is FastAPI. The backend is designed as an API-only service so the vanilla HTML, CSS, and JavaScript frontend can be hosted separately or deployed together later without changing the API design.
