# CleanPlates Local Development Guide

This guide explains how to start the CleanPlates project locally from VS Code, what each command does, when to use frontend/backend servers, and how the `Ctrl + Shift + B` shortcut works.

## Quick Answer

For the full CleanPlates app, you normally need both servers:

- Backend server: FastAPI API server
- Frontend server: Svelte/Vite website server

The easiest method is:

```text
Ctrl + Shift + B
```

Then open the frontend link shown in the terminal, usually:

```text
http://localhost:5173/
```

If port `5173` is already busy, Vite may use another port such as:

```text
http://localhost:5174/
http://localhost:5175/
```

Always open the exact frontend URL shown in the VS Code terminal.

## Project Structure

Important folders/files:

```text
CleanPlates/
  app/
    main.py              FastAPI backend entry point

  frontend/
    package.json         Frontend npm scripts live here
    vite.config.ts       Frontend dev server config

  .venv/
    Scripts/
      python.exe         Project Python environment

  .vscode/
    tasks.json           VS Code shortcut tasks
```

The backend command must be run from:

```text
C:\Users\mannu\OneDrive\Desktop\CleanPlates
```

The frontend command must be run from:

```text
C:\Users\mannu\OneDrive\Desktop\CleanPlates\frontend
```

## Method 1: Start Everything With VS Code Shortcut

Use this when you want the full app to work.

Steps:

1. Open VS Code.
2. Open the folder:

```text
C:\Users\mannu\OneDrive\Desktop\CleanPlates
```

3. Press:

```text
Ctrl + Shift + B
```

4. VS Code starts both servers:

- Backend on `http://127.0.0.1:8000`
- Frontend on `http://localhost:5173/` or another available Vite port

5. Open the frontend URL shown in the terminal.

Example:

```text
http://localhost:5173/
```

or, if Vite says port `5173` is busy:

```text
http://localhost:5175/
```

## What I Added To VS Code

I created this file:

```text
C:\Users\mannu\OneDrive\Desktop\CleanPlates\.vscode\tasks.json
```

VS Code automatically reads `.vscode/tasks.json`.

That file defines shortcuts/tasks for this project:

- `CleanPlates: Backend`
- `CleanPlates: Frontend`
- `CleanPlates: Start App (Backend + Frontend)`
- `CleanPlates: Redis (Docker, Optional)`

The combined task, `CleanPlates: Start App (Backend + Frontend)`, is marked as the default build task. That is why pressing `Ctrl + Shift + B` starts both backend and frontend.

## Method 2: Start Servers Manually

Use this if you want full control or if the VS Code task is not working.

You need two terminals.

### Terminal 1: Backend

Run this from the project root:

```powershell
cd C:\Users\mannu\OneDrive\Desktop\CleanPlates
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend URLs:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

Important:

```text
http://127.0.0.1:8000/
```

may show:

```text
Not Found
```

That is normal. The backend is an API server, not the website homepage.

### Terminal 2: Frontend

Run this from the frontend folder:

```powershell
cd C:\Users\mannu\OneDrive\Desktop\CleanPlates\frontend
npm run dev
```

Frontend URL:

```text
http://localhost:5173/
```

If Vite chooses another port, open the exact URL printed in terminal.

Example:

```text
Port 5173 is in use, trying another one...
Port 5174 is in use, trying another one...
Local: http://localhost:5175/
```

In that case, open:

```text
http://localhost:5175/
```

## Does `npm run dev` Start Both Servers?

No.

This command:

```powershell
cd C:\Users\mannu\OneDrive\Desktop\CleanPlates\frontend
npm run dev
```

starts only the frontend server.

It does not start the FastAPI backend.

For the full app, you also need the backend running:

```powershell
cd C:\Users\mannu\OneDrive\Desktop\CleanPlates
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Do You Need Both Frontend And Backend?

Usually, yes.

Use both when:

- You want to use the actual website.
- You want login/API calls to work.
- You want dashboard data to load.
- You are testing the complete app.

Use only frontend when:

- You are editing UI layout only.
- You are checking static pages/components.
- You do not need real backend API data.

Use only backend when:

- You are testing API endpoints.
- You are using FastAPI docs.
- You are checking `/health`.
- You are debugging backend logic.

## Backend vs Frontend URLs

Backend:

```text
http://127.0.0.1:8000
```

Useful backend pages:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

Frontend:

```text
http://localhost:5173/
```

or whatever port Vite prints.

The website you should open is the frontend URL, not the backend root URL.

## Why `http://127.0.0.1:8000/` Shows Not Found

This project's backend does not define a route for `/`.

So this:

```text
http://127.0.0.1:8000/
```

returns:

```text
Not Found
```

That does not mean the backend is broken.

Check this instead:

```text
http://127.0.0.1:8000/health
```

or:

```text
http://127.0.0.1:8000/docs
```

## Correct Backend Command

Correct:

```powershell
py -m uvicorn app.main:app --reload
```

Better, using the project virtual environment directly:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Incorrect:

```powershell
py -m uvicorn app.main: app --reload
```

The problem is the space after the colon:

```text
app.main: app
```

It should be:

```text
app.main:app
```

## Why `npm run dev` Failed In The Screenshot

The terminal showed this error:

```text
npm error enoent Could not read package.json
```

That happened because `npm run dev` was run from:

```text
C:\Users\mannu\OneDrive\Desktop\CleanPlates
```

But the frontend `package.json` is here:

```text
C:\Users\mannu\OneDrive\Desktop\CleanPlates\frontend\package.json
```

So the correct command is:

```powershell
cd C:\Users\mannu\OneDrive\Desktop\CleanPlates\frontend
npm run dev
```

The VS Code task fixes this by setting the frontend task's working directory to the `frontend` folder automatically.

## Why The Localhost Link Stops Working Later

Localhost links work only while the server process is running.

This will stop the server:

- Closing the VS Code terminal running the server
- Pressing `Ctrl + C` in the server terminal
- Closing VS Code if the task terminals are stopped
- Restarting/shutting down the computer

Closing only the browser tab does not stop the server.

When the link stops working, start the servers again:

```text
Ctrl + Shift + B
```

Then open the frontend URL printed in terminal.

## Why The Frontend Port Changes

Vite prefers:

```text
5173
```

But if that port is already in use, Vite automatically tries another one:

```text
5174
5175
5176
```

Example terminal message:

```text
Port 5173 is in use, trying another one...
Port 5174 is in use, trying another one...
Local: http://localhost:5175/
```

In that case, use:

```text
http://localhost:5175/
```

To get back to `5173`, stop old frontend servers first.

In VS Code, you can:

- Click the trash icon on old terminal sessions.
- Or click the terminal and press `Ctrl + C`.
- Then run `Ctrl + Shift + B` again.

## Redis And Docker

Redis is optional for basic development.

Without Redis, the backend may show warnings like:

```text
Could not connect to Redis
rate limiting and background jobs will be unavailable
```

That does not necessarily mean the app is broken.

Redis is used for things like:

- Background jobs
- ARQ worker tasks
- Some websocket/pub-sub behavior
- Rate limiting

Docker is not required to start the frontend or backend.

Docker is only a convenient way to start services like Redis.

Optional Redis command:

```powershell
cd C:\Users\mannu\OneDrive\Desktop\CleanPlates
docker compose -f docker-compose.dev.yml up -d redis
```

If Docker Desktop is not running, this command will not work. You can still run the basic frontend and backend without it.

## How The VS Code Task Works

This project has:

```text
.vscode/tasks.json
```

Inside it, there are separate tasks.

The backend task runs the backend command from the project root:

```json
"options": {
  "cwd": "${workspaceFolder}"
}
```

The frontend task runs `npm run dev` from the frontend folder:

```json
"options": {
  "cwd": "${workspaceFolder}\\frontend"
}
```

The combined task starts both:

```json
"dependsOn": [
  "CleanPlates: Backend",
  "CleanPlates: Frontend"
],
"dependsOrder": "parallel"
```

This means VS Code starts backend and frontend at the same time.

This part makes `Ctrl + Shift + B` run the combined task:

```json
"group": {
  "kind": "build",
  "isDefault": true
}
```

## Can You Create This In Other Projects?

Yes.

You can create a `.vscode/tasks.json` file in any project.

The main idea is:

- Put commands inside VS Code tasks.
- Set the correct working directory with `cwd`.
- Use a combined task with `dependsOn` to start multiple servers.
- Mark the combined task as default if you want `Ctrl + Shift + B` to run it.

## Generic Template For Other Projects

Create:

```text
.vscode/tasks.json
```

Example:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Backend",
      "type": "shell",
      "command": "your backend command here",
      "options": {
        "cwd": "${workspaceFolder}"
      },
      "isBackground": true,
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    },
    {
      "label": "Frontend",
      "type": "shell",
      "command": "npm run dev",
      "options": {
        "cwd": "${workspaceFolder}\\frontend"
      },
      "isBackground": true,
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      }
    },
    {
      "label": "Start Both",
      "dependsOn": [
        "Backend",
        "Frontend"
      ],
      "dependsOrder": "parallel",
      "problemMatcher": [],
      "group": {
        "kind": "build",
        "isDefault": true
      }
    }
  ]
}
```

After that:

```text
Ctrl + Shift + B
```

will run the default build task.

## When To Use What

Use this most of the time:

```text
Ctrl + Shift + B
```

Use this when debugging only backend:

```powershell
cd C:\Users\mannu\OneDrive\Desktop\CleanPlates
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Use this when debugging only frontend:

```powershell
cd C:\Users\mannu\OneDrive\Desktop\CleanPlates\frontend
npm run dev
```

Use this only when you need Redis features:

```powershell
cd C:\Users\mannu\OneDrive\Desktop\CleanPlates
docker compose -f docker-compose.dev.yml up -d redis
```

## Final Recommended Workflow

Daily development:

1. Open VS Code.
2. Open the `CleanPlates` folder.
3. Press:

```text
Ctrl + Shift + B
```

4. Wait for:

```text
Uvicorn running on http://127.0.0.1:8000
```

and:

```text
VITE ready
Local: http://localhost:5173/
```

5. Open the frontend URL shown by Vite.

Backend check:

```text
http://127.0.0.1:8000/health
```

Frontend website:

```text
http://localhost:5173/
```

or the exact port shown in terminal.
