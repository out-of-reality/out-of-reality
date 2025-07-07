<!-- /!\ Non OCA Context : Set here the badge of your runbot / runboat instance. -->

[![Pre-commit Status](https://github.com/out-of-reality/out-of-reality/actions/workflows/pre-commit.yml/badge.svg?branch=17.0)](https://github.com/out-of-reality/out-of-reality/actions/workflows/pre-commit.yml?query=branch%3A17.0)
[![Build Status](https://github.com/out-of-reality/out-of-reality/actions/workflows/test.yml/badge.svg?branch=17.0)](https://github.com/out-of-reality/out-of-reality/actions/workflows/test.yml?query=branch%3A17.0)
[![codecov](https://codecov.io/gh/out-of-reality/out-of-reality/branch/17.0/graph/badge.svg)](https://codecov.io/gh/out-of-reality/out-of-reality)

<!-- /!\ Non OCA Context : Set here the badge of your translation instance. -->

<!-- /!\ do not modify above this line -->

# Out of Reality - Rehabilitation System

A comprehensive Odoo-based platform for physical therapy and rehabilitation using Virtual Reality and Augmented Reality technology.

## 🎯 Overview

Out of Reality is an innovative rehabilitation platform that combines traditional physical therapy with cutting-edge VR/AR technology. The system provides a gamified approach to rehabilitation exercises, making therapy more engaging and effective for patients.

## 📦 Modules

### Core Modules

- **[clinic_management](clinic_management/)** - Complete clinic management system for patients, kinesiologists, and sessions
- **[out_of_reality_api](out_of_reality_api/)** - FastAPI-based REST API for Unity application
- **[auth_faceid](auth_faceid/)** - Facial recognition authentication system

### Features

- 👥 **Patient Management** - Complete patient profiles with health insurance integration
- 🩺 **Professional Management** - Kinesiologist profiles and session tracking
- 🎮 **Game Sessions** - Interactive rehabilitation exercises
- 📊 **Progress Tracking** - Real-time performance monitoring and reporting
- 🔐 **Facial Authentication** - Secure login using facial recognition
- 📹 **Video Processing** - Automatic video conversion and analysis
- 🏥 **Insurance Integration** - Health insurance provider management

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/out-of-reality/out-of-reality.git
   cd out-of-reality
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Odoo:**
   - Add this repository to your Odoo addons path
   - Install the required modules: `clinic_management`, `out_of_reality_api`, `auth_faceid`

4. **Setup API:**
   - Configure JWT secret key in System Parameters
   - Install FFmpeg for video processing
   - Access API documentation at `/api/out_of_reality_api/docs`

## 🏗️ Architecture

```
Out of Reality Platform
├── Game (Unity Application)
├── API Layer (FastAPI)
├── Business Logic (Odoo Modules)
└── Database (PostgreSQL)
```

### API Endpoints

- **Authentication:** `/api/out_of_reality_api/login`, `/api/out_of_reality_api/faceid_login`
- **Video Upload:** `/api/out_of_reality_api/upload/`
- **Level Management:** `/api/out_of_reality_api/levels/`
- **User Management:** `/api/out_of_reality_api/whoami`

## 📖 Documentation

Each module contains detailed documentation in their respective `readme/` folders:

- [Clinic Management Documentation](clinic_management/readme/)
- [API Documentation](out_of_reality_api/readme/)
- [FaceID Authentication Documentation](auth_faceid/readme/)

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

## 👥 Team

**Out of Reality Team:**
- Franco Leyes
- Augusto Cáceres
- Santiago Agüero

---

*Making rehabilitation accessible, engaging, and effective through technology.*

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Licenses

This repository is licensed under [AGPL-3.0](LICENSE).

However, each module can have a totally different license, as long as they adhere to Out
of reality policy. Consult each module's `__manifest__.py` file, which contains a
`license` key that explains its license.

---

<!-- /!\ Non OCA Context : Set here the full description of your organization. -->
