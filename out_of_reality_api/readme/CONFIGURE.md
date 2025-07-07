**Setup:**

1. **Configure JWT Secret Key**

   - Go to Settings → System Parameters
   - Create parameter: `jwt.secret_key` with a secure secret

2. **Install FFmpeg (for video processing)**

   ```bash
   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   
   # macOS
   brew install ffmpeg
   ```

3. **Configure API Endpoints**

   - API will be available at: `/api/out_of_reality_api/`
   - Documentation at: `/api/out_of_reality_api/docs`

4. **Configure FaceID Authentication**

   - Install and configure `auth_faceid` module
   - Setup facial recognition service
