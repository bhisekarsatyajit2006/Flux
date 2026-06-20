# Deployment Guide: Pyrefly IQ Assessment

This guide will help you deploy the assessment platform to the cloud.

## Prerequisites
- A GitHub account.
- A free account on **Render** (render.com) or **Railway** (railway.app).
- Your MongoDB connection string (e.g., from MongoDB Atlas).

---

## Option 1: Deploy to Render (Standard - No Docker)

1. **Push to GitHub**: Ensure your project structure has `backend/` and `frontend/` at the root.
2. **Create Web Service**: In Render, click "New" -> "Web Service".
3. **Environment Configuration**:
   - **Runtime**: Select `Python 3`.
   - **Region**: Choose one closest to your users.
4. **Build Command**: `pip install -r backend/requirements.txt`
5. **Start Command**: `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
6. **Environment Variables**: Add these in the "Environment" tab:
   - `MONGO_URI`: Your MongoDB Atlas string.
   - `NVIDIA_API_KEY`: Your NVIDIA NIM key.
   - `AI_PROVIDER`: `nvidia`
   - `JWT_SECRET`: A secure random string.
   - `PYTHONPATH`: `.` (optional but helpful)

---

## Option 2: Deploy to Railway (No Docker)

1. **New Project**: "Deploy from GitHub repo".
2. **Settings**:
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
3. **Variables**: Add `MONGO_URI`, `NVIDIA_API_KEY`, `AI_PROVIDER`, and `JWT_SECRET`.

---

## Option 3: Deploy to Vercel (Serverless)

Vercel is great for the IQ Test platform because it automatically handles the frontend and backend in one place.

1. **Install Vercel CLI** (Optional): `npm i -g vercel` or just use the GitHub integration.
2. **Push to GitHub**: I have already created the required `vercel.json` and `api/index.py` files for you.
3. **Connect to Vercel**:
   - Go to Vercel Dashboard -> "Add New" -> "Project" -> Import your GitHub repo.
   - Vercel will detect it as a Python project.
4. **Environment Variables**: Go to "Settings" -> "Environment Variables" and add:
   - `MONGO_URI`: Your MongoDB string.
   - `NVIDIA_API_KEY`: Your NVIDIA NIM key.
   - `AI_PROVIDER`: `nvidia`
   - `JWT_SECRET`: A secure key.
5. **Deploy**: Click "Deploy". Your app will be live at `your-project.vercel.app`.

> [!NOTE]
> Vercel Serverless Functions have a maximum execution time (10s on Free plan). If your AI analysis takes longer, consider using **Render** or **Railway** for better stability with large models.

---

## Option 4: Deploy with Docker (Cross-Platform)

## Post-Deployment Checklist

- [ ] **Verify Database**: Ensure your MongoDB Atlas IP Whitelist allows "0.0.0.0/0" (or specifically the IP of your hosting provider).
- [ ] **Test Analysis**: Take a practice test to confirm NVIDIA NIM is generating results correctly on the live URL.
- [ ] **Security**: Change your `JWT_SECRET` from the local default to something highly secure.

**Your assessment platform is now global!** 🚀
