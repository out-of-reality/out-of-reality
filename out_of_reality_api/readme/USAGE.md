**Authentication:**

1. Login with credentials: `POST /api/out_of_reality_api/login`
2. Use access token in Authorization header: `Bearer <token>`
3. Alternative: FaceID login: `POST /api/out_of_reality_api/faceid_login`

**Video Upload:**

1. Upload MP4 videos: `POST /api/out_of_reality_api/upload/`
2. Videos are automatically converted to H.264 format
3. Returns filename for further processing

**Level Management:**

1. Get first active level: `GET /api/out_of_reality_api/levels/first_active`
2. Get specific level: `GET /api/out_of_reality_api/levels/{level_id}`

**User Info:**

1. Get current user info: `GET /api/out_of_reality_api/whoami`

**API Documentation:**

- Interactive docs available at: `/api/out_of_reality_api/docs`
- OpenAPI schema at: `/api/out_of_reality_api/openapi.json`
