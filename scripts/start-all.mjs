import { spawn, execSync } from 'child_process';
import net from 'net';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '..');
const BACKEND_DIR = path.resolve(ROOT_DIR, 'backend');
const FRONTEND_DIR = path.resolve(ROOT_DIR, 'frontend');

// ANSI Color Helpers
const C = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  cyan: '\x1b[36m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  red: '\x1b[31m',
};

const log = (prefix, color, message) => {
  const lines = message.toString().split(/\r?\n/);
  for (const line of lines) {
    if (line.trim().length > 0) {
      console.log(`${color}[${prefix}]${C.reset} ${line}`);
    }
  }
};

// 1. Verify / Start PostgreSQL
const checkPostgres = () => {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    socket.setTimeout(2000);

    socket.on('connect', () => {
      log('PostgreSQL', C.green, 'Service active & listening on 127.0.0.1:5432.');
      socket.destroy();
      resolve(true);
    });

    socket.on('error', () => {
      socket.destroy();
      log('PostgreSQL', C.yellow, 'Port 5432 not responding. Attempting to start Windows Service...');
      try {
        execSync('net start postgresql-x64-16', { stdio: 'pipe' });
        log('PostgreSQL', C.green, 'Successfully started postgresql-x64-16 service.');
        resolve(true);
      } catch (err) {
        log(
          'PostgreSQL',
          C.red,
          'Warning: Could not start PostgreSQL service automatically. If database operations fail, start PostgreSQL in services.msc or pgAdmin.'
        );
        resolve(false);
      }
    });

    socket.on('timeout', () => {
      socket.destroy();
      resolve(false);
    });

    socket.connect(5432, '127.0.0.1');
  });
};

// 2. Locate Python Interpreter
const getPythonPath = () => {
  const venvWindows = path.join(BACKEND_DIR, 'venv', 'Scripts', 'python.exe');
  const venvUnix = path.join(BACKEND_DIR, 'venv', 'bin', 'python');

  if (fs.existsSync(venvWindows)) return venvWindows;
  if (fs.existsSync(venvUnix)) return venvUnix;
  return 'python';
};

// Child Process tracker for graceful shutdown
const children = [];

const killAll = () => {
  for (const child of children) {
    if (child && !child.killed) {
      try {
        if (process.platform === 'win32') {
          execSync(`taskkill /F /T /PID ${child.pid}`, { stdio: 'ignore' });
        } else {
          child.kill('SIGTERM');
        }
      } catch {
        // Process might already be dead
      }
    }
  }
};

process.on('SIGINT', () => {
  console.log(`\n${C.yellow}Shutting down servers...${C.reset}`);
  killAll();
  process.exit(0);
});

process.on('SIGTERM', () => {
  killAll();
  process.exit(0);
});

process.on('exit', () => {
  killAll();
});

// Main Orchestrator
async function startAll() {
  console.log(`\n${C.bright}${C.blue}======================================================${C.reset}`);
  console.log(`${C.bright}${C.blue} 🚀 Scientific Document Manager — Unified Dev Runner ${C.reset}`);
  console.log(`${C.bright}${C.blue}======================================================${C.reset}\n`);

  // Step 1: Check PostgreSQL
  await checkPostgres();

  // Step 2: Launch Django Backend
  const pythonPath = getPythonPath();
  log('Backend', C.cyan, `Using Python: ${pythonPath}`);
  log('Backend', C.cyan, 'Starting Django API server on http://127.0.0.1:8000 ...');

  const backendProc = spawn(pythonPath, ['manage.py', 'runserver', '8000'], {
    cwd: BACKEND_DIR,
    shell: false,
  });
  children.push(backendProc);

  backendProc.stdout.on('data', (data) => log('Backend', C.cyan, data));
  backendProc.stderr.on('data', (data) => log('Backend', C.cyan, data));
  backendProc.on('error', (err) => log('Backend', C.red, `Failed to start backend: ${err.message}`));

  // Step 3: Launch Frontend
  log('Frontend', C.magenta, 'Starting Vite dev server on http://localhost:5173 ...');

  const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm';
  const frontendProc = spawn(npmCmd, ['run', 'dev'], {
    cwd: FRONTEND_DIR,
    shell: false,
  });
  children.push(frontendProc);

  frontendProc.stdout.on('data', (data) => log('Frontend', C.magenta, data));
  frontendProc.stderr.on('data', (data) => log('Frontend', C.magenta, data));
  frontendProc.on('error', (err) => log('Frontend', C.red, `Failed to start frontend: ${err.message}`));

  console.log(`\n${C.green}✔ Systems initializing in parallel.${C.reset} Press ${C.bright}Ctrl+C${C.reset} to stop all services.\n`);
}

startAll();
