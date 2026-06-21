const { app, BrowserWindow } = require("electron");
const path = require("path");

const isDev = process.env.ELECTRON_DEV === "1";

function shellDistPath(...segments) {
  return path.join(__dirname, "../../shell/dist", ...segments);
}

function resolveShellIndex() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "shell", "index.html");
  }
  return shellDistPath("index.html");
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: "SceneEnglish",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    win.loadURL("http://127.0.0.1:5173");
    win.webContents.openDevTools({ mode: "detach" });
  } else {
    win.loadFile(resolveShellIndex());
  }
}

app.whenReady().then(() => {
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
