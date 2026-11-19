import os
import json
import re
import urllib.parse
import urllib.request
import base64
import webbrowser
import threading
import tkinter as tk
from tkinter import filedialog
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8765
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}

DEFAULT_SLOTS = [
    {
        "id": "slot_1",
        "title": "1. Trigger Word",
        "active": ["char_a | Character A trigger", "char_b | Character B trigger"],
        "basket": [],
        "multi": False
    },
    {
        "id": "slot_2",
        "title": "2. Subject & Build",
        "active": [
            "a young woman | Young woman",
            "a young man | Young man",
            "slender build | Slender build",
            "stocky build | Stocky build"
        ],
        "basket": [],
        "multi": False
    },
    {
        "id": "slot_3",
        "title": "3. Camera Angle",
        "active": [
            "front view | Front view",
            "three-quarter view | Three-quarter view",
            "side view | Side view"
        ],
        "basket": ["back view | Back view"],
        "multi": False
    },
    {
        "id": "slot_4",
        "title": "4. Shot Type",
        "active": [
            "close-up | Close-up",
            "half body | Half body",
            "full body | Full body"
        ],
        "basket": ["upper body | Upper body"],
        "multi": False
    },
    {
        "id": "slot_5",
        "title": "5. Head Pose (Optional Multi)",
        "active": [
            "head tilted to the side | Head tilted",
            "chin slightly raised | Chin slightly raised",
            "head lowered | Head lowered",
            "head turned to the side | Head turned",
            "looking over shoulder | Looking over shoulder"
        ],
        "basket": [],
        "multi": True
    },
    {
        "id": "slot_6",
        "title": "6. Expression",
        "active": [
            "neutral expression | Neutral",
            "smiling | Smiling",
            "frowning | Frowning",
            "serious expression | Serious"
        ],
        "basket": [],
        "multi": False
    },
    {
        "id": "slot_7",
        "title": "7. Outfit",
        "active": [
            "wearing a casual jacket | Casual jacket",
            "wearing a formal suit | Formal suit",
            "wearing traditional attire | Traditional attire"
        ],
        "basket": [],
        "multi": False
    },
    {
        "id": "slot_8",
        "title": "8. Hairstyle",
        "active": [
            "short black hair | Short black hair",
            "long black hair | Long black hair"
        ],
        "basket": [],
        "multi": False
    },
    {
        "id": "slot_9",
        "title": "9. Background",
        "active": [
            "white background | White background",
            "simple background | Simple background"
        ],
        "basket": ["grey background | Grey background"],
        "multi": False
    }
]

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>xd_char_tagger - Character Tagging Workbench</title>
<style>
  :root {
    --bg: #121417;
    --panel: #1b1e23;
    --card: #23272e;
    --border: #323842;
    --accent: #3b82f6;
    --accent-hover: #2563eb;
    --selected: #10b981;
    --selected-bg: rgba(16, 185, 129, 0.18);
    --text: #e5e7eb;
    --muted: #9ca3af;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  header {
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    padding: 8px 12px;
    display: flex;
    gap: 6px;
    align-items: center;
    flex-wrap: wrap;
  }
  header input[type="text"] {
    background: var(--bg);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 5px 8px;
    border-radius: 6px;
    font-size: 12.5px;
  }
  #folderInput { width: 175px; }
  #ollamaModel { width: 110px; }
  button {
    background: var(--card);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 5px 9px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
    transition: all 0.15s;
    white-space: nowrap;
  }
  button:hover { border-color: var(--accent); background: #2c313a; }
  button.primary { background: var(--accent); border-color: var(--accent); color: #fff; font-weight: 500; }
  button.primary:hover { background: var(--accent-hover); }
  button.ai-btn { background: #7c3aed; border-color: #7c3aed; color: #fff; }
  button.ai-btn:hover { background: #6d28d9; }
  button.ai-all-btn { background: #9333ea; border-color: #9333ea; color: #fff; font-weight: 500; }
  button.ai-all-btn:hover { background: #7e22ce; }
  button.rename-btn { background: #d97706; border-color: #d97706; color: #fff; font-weight: 500; }
  button.rename-btn:hover { background: #b45309; }
  button.add-slot-btn { background: #059669; border-color: #059669; color: #fff; }
  button.add-slot-btn:hover { background: #047857; }
  button.del-btn { background: #b91c1c; border-color: #991b1b; color: #fff; }
  button.del-btn:hover { background: #991b1b; }
  button.lang-btn { background: #0284c7; border-color: #0284c7; color: #fff; font-weight: 600; }
  button.lang-btn:hover { background: #0369a1; }
  .status-badge {
    margin-left: auto;
    font-size: 12px;
    color: var(--selected);
  }

  main {
    display: flex;
    flex: 1;
    overflow: hidden;
  }
  #sidebar {
    width: 220px;
    background: var(--panel);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
  }
  #imgCount {
    padding: 8px 12px;
    font-size: 12px;
    color: var(--muted);
    border-bottom: 1px solid var(--border);
  }
  #fileList {
    flex: 1;
    overflow-y: auto;
    list-style: none;
  }
  #fileList li {
    padding: 8px 12px;
    font-size: 13px;
    cursor: pointer;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    display: flex;
    justify-content: space-between;
    align-items: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  #fileList li:hover { background: var(--card); }
  #fileList li.active { background: var(--accent); color: #fff; font-weight: 500; }
  #fileList li .dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--selected); flex-shrink: 0; margin-left: 6px;
  }
  #fileList li .dot.empty { background: #4b5563; }

  #centerPane {
    width: 36%;
    min-width: 310px;
    background: #0d0f12;
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    padding: 12px;
    gap: 12px;
  }
  #previewBox {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    background: #16191e;
    border-radius: 8px;
    border: 1px solid var(--border);
    position: relative;
  }
  #previewImg {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }
  #navHint {
    position: absolute;
    bottom: 8px;
    right: 10px;
    background: rgba(0,0,0,0.65);
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 11px;
    color: var(--muted);
  }
  #outputBox {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px;
  }
  #outputBox label {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 6px;
  }
  #finalPrompt {
    width: 100%;
    height: 95px;
    background: var(--bg);
    border: 1px solid var(--border);
    color: #a7f3d0;
    padding: 8px;
    border-radius: 6px;
    font-size: 13px;
    line-height: 1.5;
    resize: none;
  }

  #rightContainer {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  #slotsPane {
    flex: 1;
    overflow-y: auto;
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .slot-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 12px;
  }
  .slot-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    gap: 6px;
  }
  .slot-title-input {
    background: var(--bg);
    border: 1px solid var(--border);
    color: #f3f4f6;
    font-size: 13px;
    font-weight: 600;
    padding: 3px 6px;
    border-radius: 4px;
    flex: 1;
  }
  .slot-actions {
    display: flex;
    gap: 6px;
    align-items: center;
  }
  .slot-actions label {
    font-size: 11.5px;
    color: var(--muted);
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 3px;
    background: rgba(255,255,255,0.05);
    padding: 2px 6px;
    border-radius: 4px;
    border: 1px solid var(--border);
  }
  .slot-actions label:hover { border-color: var(--accent); color: var(--text); }
  .slot-actions input[type="checkbox"] {
    cursor: pointer;
    accent-color: var(--accent);
  }
  .slot-actions button {
    padding: 2px 6px;
    font-size: 11px;
  }
  .tag-zone {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    min-height: 32px;
    padding: 4px;
    border-radius: 6px;
  }
  .tag-chip {
    background: var(--card);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 5px 10px;
    border-radius: 5px;
    font-size: 12.5px;
    cursor: pointer;
    user-select: none;
    transition: all 0.12s;
    display: flex;
    flex-direction: column;
    gap: 2px;
    position: relative;
  }
  .tag-chip:hover { border-color: #6b7280; }
  .tag-chip.selected {
    background: var(--selected-bg);
    border-color: var(--selected);
    color: #34d399;
    font-weight: 600;
    box-shadow: 0 0 0 1px var(--selected);
  }
  .tag-en { font-family: monospace; font-size: 12px; }
  .tag-zh { font-size: 11px; color: var(--muted); }
  .tag-chip.selected .tag-zh { color: #6ee7b7; }

  .basket-box {
    margin-top: 8px;
    padding: 6px 8px;
    border: 1px dashed #3f4652;
    border-radius: 6px;
    background: rgba(0, 0, 0, 0.22);
    opacity: 0.65;
    transition: opacity 0.2s;
  }
  .basket-box:hover, .basket-box.drag-over {
    opacity: 1;
    border-color: var(--accent);
  }
  .basket-label {
    font-size: 11px;
    color: var(--muted);
    margin-bottom: 4px;
  }
  .basket-zone {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    min-height: 24px;
  }
  .basket-zone .tag-chip {
    padding: 3px 8px;
    background: #181b20;
  }
  .basket-zone .tag-en { font-size: 11px; }

  #globalBasketPane {
    background: #16191e;
    border-top: 1px solid var(--border);
    padding: 8px 14px;
    max-height: 120px;
    overflow-y: auto;
  }
  #globalBasketPane .basket-label {
    font-weight: bold;
    color: #93c5fd;
    margin-bottom: 4px;
    font-size: 12px;
  }
</style>
</head>
<body>

<header>
  <input type="text" id="folderInput" placeholder="选择文件夹">
  <button class="primary" id="btnBrowse" onclick="browseFolder()">📂 选择</button>
  <button class="add-slot-btn" id="btnAddSlot" onclick="addNewSlot()">➕ 新增框</button>
  <button class="del-btn" id="btnDelFile" onclick="deleteCurrentFile()">🗑️ 删当前图</button>
  <button id="btnApplyAll" onclick="applyFixedToAll()">📌 批量固定</button>
  <button class="rename-btn" id="btnRename" onclick="openRenameModal()">🧹 一键整理命名</button>
  <button class="lang-btn" id="btnLang" onclick="toggleLang()" title="切换中英文界面提示">🌐 ENG/CN</button>
  <span style="border-left:1px solid var(--border); height:20px; margin:0 2px;"></span>
  <input type="text" id="ollamaModel" value="qwen2.5vl:7b" title="Ollama 模型">
  <button class="ai-btn" id="btnAiCur" onclick="aiPrefillCurrent()">✨ AI 填当前</button>
  <button class="ai-all-btn" id="btnAiAll" onclick="aiPrefillAll()">🚀 AI 批量填全部</button>
  <span class="status-badge" id="statusText">等待选择文件夹...</span>
</header>

<main>
  <div id="sidebar">
    <div id="imgCount">图片列表 (0)</div>
    <ul id="fileList"></ul>
  </div>

  <div id="centerPane">
    <div id="previewBox">
      <img id="previewImg" src="" alt="预览图">
      <div id="navHint">快捷键: ↑ 上一张 | ↓ 下一张 (自动保存)</div>
    </div>
    <div id="outputBox">
      <label>
        <span id="lblFinalPrompt">最终生成的 .txt 标注 (纯英文)</span>
        <span id="saveIndicator" style="color:#10b981;"></span>
      </label>
      <textarea id="finalPrompt" readonly></textarea>
    </div>
  </div>

  <div id="rightContainer">
    <div id="slotsPane"></div>
    <div id="globalBasketPane" ondragover="event.preventDefault()" ondrop="handleGlobalDrop(event)">
      <div class="basket-label" id="lblGlobalBasket">🧺 全局总 Basket（删除大框时里面的 Tag 会自动存放在这里，可拖回任意框）</div>
      <div class="basket-zone" id="globalBasketZone"></div>
    </div>
  </div>
</main>

<script>
let lang = "zh";

const I18N = {
  zh: {
    pageTitle: "xd_char_tagger - 角色结构化打标工作台",
    folderPlaceholder: "选择文件夹",
    browse: "📂 选择",
    addSlot: "➕ 新增框",
    delFile: "🗑️ 删当前图",
    applyAll: "📌 批量固定",
    rename: "🧹 一键整理命名",
    langBtn: "🌐 ENG/CN",
    langTitle: "点击切换英文提示 / 再点切回中文",
    modelTitle: "Ollama 模型（可选）",
    aiCur: "✨ AI 填当前",
    aiAll: "🚀 AI 批量填全部",
    waitingFolder: "等待选择文件夹...",
    imgListCount: (n) => `图片列表 (${n})`,
    previewAlt: "预览图",
    navHint: "快捷键: ↑ 上一张 | ↓ 下一张 (自动保存)",
    finalPromptLabel: "最终生成的 .txt 标注 (纯英文)",
    savedBadge: "✓ 已自动保存",
    globalBasketLabel: "🧺 全局总 Basket（删除大框时里面的 Tag 会自动存放在这里，可拖回任意框）",
    alertPickFolder: "请先选择文件夹路径！",
    loadedCount: (n) => `已加载 ${n} 张图片`,
    noImagesInFolder: "文件夹内未找到图片",
    confirmDelFile: (name) => `确定要彻底删除图片 "${name}" 及其同名 .txt 文件吗？`,
    deletedNext: "已删除，切换至下一张",
    folderEmptyNow: "文件夹已无图片",
    multiLabel: " 多选",
    moveUpTitle: "大框上移",
    moveDownTitle: "大框下移",
    addTagBtn: "+ 新增",
    delSlotBtn: "🗑️ 删框",
    slotBasketLabel: "🧺 框内 Basket（右键删除，双击修改）",
    editTagPrompt: "修改 Tag（格式: 英文 | 中文）：",
    confirmDelTag: (en) => `彻底删除 "${en}"？`,
    confirmDelSlotTag: (en) => `删除词 "${en}"？`,
    newSlotPrompt: "请输入新分类大框的名字：",
    newSlotDefault: "新分类标签",
    confirmDelSlot: (title) => `确定要删除大框【${title}】吗？里面的 Tag 会收入底部全局 Basket。`,
    newTagPrompt: "请输入新 Tag（格式: 英文 | 中文，例如: blue eyes | 蓝眼睛）：",
    confirmApplyAll: (n) => `确定将当前选中的各项批量应用到全部 ${n} 张图片吗？`,
    applyingAll: "正在批量应用...",
    applyAllDone: "批量应用完成！",
    renamePrompt: "请输入数据集文件名前缀（例如输入 tjb，将整理为 tjb1、tjb2...）：",
    confirmRename: (prefix, n) => `即将把文件夹内全部 ${n} 张图片及对应 .txt 重命名为 ${prefix}1、${prefix}2...，确定开始吗？`,
    renamingProgress: (prefix, n) => `正在整理命名为 ${prefix}1 ~ ${prefix}${n}...`,
    renameDone: (prefix, n) => `✨ 整理完成！已重命名为 ${prefix}1 ~ ${prefix}${n}`,
    aiRequesting: (model) => `正在请求本地 ${model} 识别当前图...`,
    aiNoMatch: "AI 未匹配到任何预设词",
    aiMatchedCount: (n) => `AI 成功匹配了 ${n} 项！`,
    confirmAiAll: (model, n) => `即将让 ${model} 自动识别文件夹内全部 ${n} 张图片并保存标签，确定开始吗？`,
    aiBatchProgress: (i, n, name) => `⏳ 批量识别进度 (${i}/${n}): 正在处理 ${name}...`,
    aiBatchError: (name, err) => `处理 ${name} 时出错: ${err}`,
    aiBatchDone: (n) => `🎉 全部 ${n} 张图片 AI 预填完成！`
  },
  en: {
    pageTitle: "xd_char_tagger - Character Tagging Workbench",
    folderPlaceholder: "Select folder",
    browse: "📂 Browse",
    addSlot: "➕ Add Slot",
    delFile: "🗑️ Del Image",
    applyAll: "📌 Apply All",
    rename: "🧹 Batch Rename",
    langBtn: "🌐 ENG/CN",
    langTitle: "Switch to Chinese / Switch to English",
    modelTitle: "Ollama Model (Optional)",
    aiCur: "✨ AI Current",
    aiAll: "🚀 AI All",
    waitingFolder: "Waiting for folder...",
    imgListCount: (n) => `Images (${n})`,
    previewAlt: "Preview",
    navHint: "Keys: ↑ Prev | ↓ Next (Auto-saved)",
    finalPromptLabel: "Generated .txt Caption (English)",
    savedBadge: "✓ Auto-saved",
    globalBasketLabel: "🧺 Global Basket (Tags from deleted slots land here; drag back to any slot)",
    alertPickFolder: "Please select a folder path first!",
    loadedCount: (n) => `Loaded ${n} images`,
    noImagesInFolder: "No images found in folder",
    confirmDelFile: (name) => `Permanently delete image "${name}" and its matching .txt file?`,
    deletedNext: "Deleted, moved to next image",
    folderEmptyNow: "No images left in folder",
    multiLabel: " Multi",
    moveUpTitle: "Move slot up",
    moveDownTitle: "Move slot down",
    addTagBtn: "+ Add",
    delSlotBtn: "🗑️ Del Slot",
    slotBasketLabel: "🧺 Slot Basket (Right-click to delete, double-click to edit)",
    editTagPrompt: "Edit Tag (format: EN | ZH):",
    confirmDelTag: (en) => `Permanently delete "${en}"?`,
    confirmDelSlotTag: (en) => `Delete tag "${en}"?`,
    newSlotPrompt: "Enter new category slot title:",
    newSlotDefault: "New Category",
    confirmDelSlot: (title) => `Delete slot [${title}]? Its tags will move to Global Basket.`,
    newTagPrompt: "Enter new Tag (format: EN | ZH, e.g. blue eyes | Blue eyes):",
    confirmApplyAll: (n) => `Apply current selections to all ${n} images?`,
    applyingAll: "Applying to all images...",
    applyAllDone: "Applied to all images!",
    renamePrompt: "Dataset filename prefix? (e.g. tjb -> tjb1, tjb2...):",
    confirmRename: (prefix, n) => `Rename all ${n} images and matching .txt files to ${prefix}1, ${prefix}2...?`,
    renamingProgress: (prefix, n) => `Renaming to ${prefix}1 ~ ${prefix}${n}...`,
    renameDone: (prefix, n) => `✨ Renamed to ${prefix}1 ~ ${prefix}${n}`,
    aiRequesting: (model) => `Requesting local ${model} for current image...`,
    aiNoMatch: "AI matched no preset tags",
    aiMatchedCount: (n) => `AI matched ${n} slot(s)!`,
    confirmAiAll: (model, n) => `Run ${model} on all ${n} images and auto-save .txt tags?`,
    aiBatchProgress: (i, n, name) => `⏳ AI Batch (${i}/${n}): Processing ${name}...`,
    aiBatchError: (name, err) => `Error on ${name}: ${err}`,
    aiBatchDone: (n) => `🎉 AI prefill finished for all ${n} images!`
  }
};

function t(key, ...args) {
  const dict = I18N[lang] || I18N.zh;
  const val = dict[key];
  return typeof val === "function" ? val(...args) : val;
}

function applyStaticI18N() {
  document.title = t("pageTitle");
  document.getElementById("folderInput").placeholder = t("folderPlaceholder");
  document.getElementById("btnBrowse").textContent = t("browse");
  document.getElementById("btnAddSlot").textContent = t("addSlot");
  document.getElementById("btnDelFile").textContent = t("delFile");
  document.getElementById("btnApplyAll").textContent = t("applyAll");
  document.getElementById("btnRename").textContent = t("rename");
  document.getElementById("btnLang").textContent = t("langBtn");
  document.getElementById("btnLang").title = t("langTitle");
  document.getElementById("ollamaModel").title = t("modelTitle");
  document.getElementById("btnAiCur").textContent = t("aiCur");
  document.getElementById("btnAiAll").textContent = t("aiAll");
  document.getElementById("previewImg").alt = t("previewAlt");
  document.getElementById("navHint").textContent = t("navHint");
  document.getElementById("lblFinalPrompt").textContent = t("finalPromptLabel");
  document.getElementById("lblGlobalBasket").textContent = t("globalBasketLabel");
  document.getElementById("imgCount").textContent = t("imgListCount", files.length);
  if (!currentFolder) {
    document.getElementById("statusText").textContent = t("waitingFolder");
  }
}

function toggleLang() {
  lang = (lang === "zh") ? "en" : "zh";
  applyStaticI18N();
  renderSlots();
  renderGlobalBasket();
}

let currentFolder = "";
let files = [];
let currentIndex = -1;
let slotsConfig = [];
let globalBasket = [];
let currentSelections = {};
let draggedData = null;
let stopBatchFlag = false;
let legacyTagMap = {};

function setStatus(msg, isError = false) {
  const el = document.getElementById("statusText");
  el.textContent = msg;
  el.style.color = isError ? "#ef4444" : "#10b981";
}

async function browseFolder() {
  const res = await fetch("/api/browse", { method: "POST" });
  const data = await res.json();
  if (data.folder) {
    document.getElementById("folderInput").value = data.folder;
    loadFolder(data.folder);
  }
}

async function loadFolder(targetFolder) {
  const folder = targetFolder || document.getElementById("folderInput").value.trim();
  if (!folder) return alert(t("alertPickFolder"));
  
  const res = await fetch("/api/load", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ folder })
  });
  const data = await res.json();
  if (data.error) return setStatus(data.error, true);

  currentFolder = folder;
  files = data.files;
  slotsConfig = data.config.slots || [];
  globalBasket = data.config.global_basket || [];
  
  rebuildLegacyMap();
  renderSlots();
  renderGlobalBasket();
  renderFileList();
  if (files.length > 0) {
    selectImage(0);
    setStatus(t("loadedCount", files.length));
  } else {
    setStatus(t("noImagesInFolder"), true);
  }
}

function rebuildLegacyMap() {
  slotsConfig.forEach(slot => {
    [...slot.active, ...slot.basket].forEach(item => {
      const en = parseItem(item).en.toLowerCase();
      legacyTagMap[en] = item;
    });
  });
}

function renderFileList() {
  const ul = document.getElementById("fileList");
  document.getElementById("imgCount").textContent = t("imgListCount", files.length);
  ul.innerHTML = "";
  files.forEach((f, idx) => {
    const li = document.createElement("li");
    if (idx === currentIndex) li.classList.add("active");
    li.innerHTML = `<span>${idx + 1}. ${f.name}</span><span class="dot ${f.has_txt ? '' : 'empty'}"></span>`;
    li.onclick = () => selectImage(idx);
    ul.appendChild(li);
  });
}

async function selectImage(idx) {
  if (files.length === 0) {
    currentIndex = -1;
    document.getElementById("previewImg").src = "";
    document.getElementById("finalPrompt").value = "";
    renderFileList();
    return;
  }
  if (idx < 0) idx = 0;
  if (idx >= files.length) idx = files.length - 1;
  currentIndex = idx;
  renderFileList();
  const activeLi = document.querySelector("#fileList li.active");
  if (activeLi) activeLi.scrollIntoView({ block: "nearest" });

  const fileObj = files[idx];
  document.getElementById("previewImg").src = `/api/image?folder=${encodeURIComponent(currentFolder)}&name=${encodeURIComponent(fileObj.name)}&t=${Date.now()}`;

  const res = await fetch(`/api/caption?folder=${encodeURIComponent(currentFolder)}&name=${encodeURIComponent(fileObj.name)}`);
  const data = await res.json();
  parseCaptionToSelections(data.caption || "");
  updateSlotHighlights();
  updateFinalPromptText(false);
}

async function deleteCurrentFile() {
  if (currentIndex < 0 || currentIndex >= files.length) return;
  const fileObj = files[currentIndex];
  if (!confirm(t("confirmDelFile", fileObj.name))) return;

  const res = await fetch("/api/delete_file", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ folder: currentFolder, name: fileObj.name })
  });
  const data = await res.json();
  if (data.error) return setStatus(data.error, true);

  files.splice(currentIndex, 1);
  if (currentIndex >= files.length) currentIndex = files.length - 1;
  renderFileList();
  if (files.length > 0) {
    selectImage(currentIndex);
    setStatus(t("deletedNext"));
  } else {
    document.getElementById("previewImg").src = "";
    document.getElementById("finalPrompt").value = "";
    setStatus(t("folderEmptyNow"));
  }
}

function parseCaptionToSelections(caption) {
  currentSelections = {};
  if (!caption.trim()) return;
  let remaining = caption.trim();
  
  slotsConfig.forEach(slot => {
    const activeItems = [...slot.active];
    activeItems.sort((a, b) => b.length - a.length);

    if (slot.multi) {
      const selectedList = [];
      activeItems.forEach(item => {
        const en = parseItem(item).en;
        const regex = new RegExp(`(^|,\\s*)${escapeRegExp(en)}(\\s*,|$)`, 'i');
        if (regex.test(remaining)) {
          selectedList.push(item);
        } else {
          for (const [oldEn, mappedItem] of Object.entries(legacyTagMap)) {
            if (mappedItem === item) {
              const oldRegex = new RegExp(`(^|,\\s*)${escapeRegExp(oldEn)}(\\s*,|$)`, 'i');
              if (oldRegex.test(remaining)) {
                selectedList.push(item);
                break;
              }
            }
          }
        }
      });
      if (selectedList.length > 0) currentSelections[slot.id] = selectedList;
    } else {
      let matched = false;
      for (const item of activeItems) {
        const en = parseItem(item).en;
        const regex = new RegExp(`(^|,\\s*)${escapeRegExp(en)}(\\s*,|$)`, 'i');
        if (regex.test(remaining)) {
          currentSelections[slot.id] = item;
          matched = true;
          break;
        }
      }
      if (!matched) {
        for (const item of activeItems) {
          for (const [oldEn, mappedItem] of Object.entries(legacyTagMap)) {
            if (mappedItem === item) {
              const regex = new RegExp(`(^|,\\s*)${escapeRegExp(oldEn)}(\\s*,|$)`, 'i');
              if (regex.test(remaining)) {
                currentSelections[slot.id] = item;
                matched = true;
                break;
              }
            }
          }
          if (matched) break;
        }
      }
    }
  });
}

function parseItem(itemStr) {
  if (itemStr.includes('|')) {
    const parts = itemStr.split('|');
    return { en: parts[0].trim(), zh: parts[1].trim() };
  }
  return { en: itemStr.trim(), zh: "" };
}

function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function renderSlots() {
  const container = document.getElementById("slotsPane");
  container.innerHTML = "";

  slotsConfig.forEach((slot, sIdx) => {
    const card = document.createElement("div");
    card.className = "slot-card";

    const header = document.createElement("div");
    header.className = "slot-header";
    
    const titleInput = document.createElement("input");
    titleInput.type = "text";
    titleInput.className = "slot-title-input";
    titleInput.value = slot.title;
    titleInput.onchange = (e) => {
      slot.title = e.target.value;
      saveConfig();
    };
    header.appendChild(titleInput);

    const actions = document.createElement("div");
    actions.className = "slot-actions";
    
    const multiLabel = document.createElement("label");
    const multiCheckbox = document.createElement("input");
    multiCheckbox.type = "checkbox";
    multiCheckbox.checked = !!slot.multi;
    multiCheckbox.onchange = (e) => {
      slot.multi = e.target.checked;
      if (!slot.multi && Array.isArray(currentSelections[slot.id])) {
        const arr = currentSelections[slot.id];
        currentSelections[slot.id] = arr.length > 0 ? arr[0] : undefined;
      } else if (slot.multi && typeof currentSelections[slot.id] === 'string') {
        currentSelections[slot.id] = [currentSelections[slot.id]];
      }
      saveConfig();
      renderSlots();
      updateFinalPromptText(true);
    };
    multiLabel.appendChild(multiCheckbox);
    multiLabel.appendChild(document.createTextNode(t("multiLabel")));
    actions.appendChild(multiLabel);

    if (sIdx > 0) {
      const upBtn = document.createElement("button");
      upBtn.textContent = "▲";
      upBtn.title = t("moveUpTitle");
      upBtn.onclick = () => moveSlot(sIdx, -1);
      actions.appendChild(upBtn);
    }
    if (sIdx < slotsConfig.length - 1) {
      const downBtn = document.createElement("button");
      downBtn.textContent = "▼";
      downBtn.title = t("moveDownTitle");
      downBtn.onclick = () => moveSlot(sIdx, 1);
      actions.appendChild(downBtn);
    }

    const addBtn = document.createElement("button");
    addBtn.textContent = t("addTagBtn");
    addBtn.onclick = () => addCustomTag(sIdx);
    actions.appendChild(addBtn);

    const delBtn = document.createElement("button");
    delBtn.textContent = t("delSlotBtn");
    delBtn.style.cssText = "background:#7f1d1d; border-color:#991b1b; color:#fca5a5;";
    delBtn.onclick = () => deleteSlot(sIdx);
    actions.appendChild(delBtn);

    header.appendChild(actions);
    card.appendChild(header);

    const activeZone = document.createElement("div");
    activeZone.className = "tag-zone";
    activeZone.ondragover = e => e.preventDefault();
    activeZone.ondrop = e => handleDrop(e, sIdx, "active");
    slot.active.forEach(item => {
      activeZone.appendChild(createTagChip(item, sIdx, "active"));
    });
    card.appendChild(activeZone);

    const basketBox = document.createElement("div");
    basketBox.className = "basket-box";
    basketBox.ondragover = e => { e.preventDefault(); basketBox.classList.add("drag-over"); };
    basketBox.ondragleave = () => basketBox.classList.remove("drag-over");
    basketBox.ondrop = e => { basketBox.classList.remove("drag-over"); handleDrop(e, sIdx, "basket"); };

    const bLabel = document.createElement("div");
    bLabel.className = "basket-label";
    bLabel.textContent = t("slotBasketLabel");
    basketBox.appendChild(bLabel);

    const basketZone = document.createElement("div");
    basketZone.className = "basket-zone";
    slot.basket.forEach(item => {
      basketZone.appendChild(createTagChip(item, sIdx, "basket"));
    });
    basketBox.appendChild(basketZone);
    card.appendChild(basketBox);

    container.appendChild(card);
  });
  updateSlotHighlights();
}

function moveSlot(index, direction) {
  const targetIndex = index + direction;
  if (targetIndex < 0 || targetIndex >= slotsConfig.length) return;
  const temp = slotsConfig[index];
  slotsConfig[index] = slotsConfig[targetIndex];
  slotsConfig[targetIndex] = temp;
  saveConfig();
  renderSlots();
  updateFinalPromptText(true);
}

function renderGlobalBasket() {
  const zone = document.getElementById("globalBasketZone");
  zone.innerHTML = "";
  globalBasket.forEach((item, gIdx) => {
    const parsed = parseItem(item);
    const chip = document.createElement("div");
    chip.className = "tag-chip";
    chip.draggable = true;
    chip.innerHTML = `<span class="tag-en">${parsed.en}</span>${parsed.zh ? '<span class="tag-zh">'+parsed.zh+'</span>' : ''}`;
    
    chip.ondragstart = () => { draggedData = { fromGlobal: true, item, gIdx }; };
    
    chip.ondblclick = () => {
      const oldEn = parsed.en.toLowerCase();
      const newRaw = prompt(t("editTagPrompt"), item);
      if (!newRaw || !newRaw.trim()) return;
      const clean = newRaw.trim();
      globalBasket[gIdx] = clean;
      legacyTagMap[oldEn] = clean;
      saveConfig();
      renderGlobalBasket();
    };

    chip.oncontextmenu = (e) => {
      e.preventDefault();
      if (confirm(t("confirmDelTag", parsed.en))) {
        globalBasket.splice(gIdx, 1);
        saveConfig();
        renderGlobalBasket();
      }
    };
    zone.appendChild(chip);
  });
}

function createTagChip(item, sIdx, zoneType) {
  const slot = slotsConfig[sIdx];
  const parsed = parseItem(item);
  const chip = document.createElement("div");
  chip.className = "tag-chip";
  chip.innerHTML = `<span class="tag-en">${parsed.en}</span>${parsed.zh ? '<span class="tag-zh">'+parsed.zh+'</span>' : ''}`;
  chip.draggable = true;
  chip.dataset.slotId = slot.id;
  chip.dataset.item = item;

  chip.onclick = () => {
    const slotId = slot.id;
    if (zoneType === "basket") {
      slot.basket = slot.basket.filter(t => t !== item);
      slot.active.push(item);
      if (slot.multi) {
        if (!currentSelections[slotId]) currentSelections[slotId] = [];
        if (!currentSelections[slotId].includes(item)) currentSelections[slotId].push(item);
      } else {
        currentSelections[slotId] = item;
      }
      saveConfig();
      renderSlots();
    } else {
      if (slot.multi) {
        if (!currentSelections[slotId]) currentSelections[slotId] = [];
        const idx = currentSelections[slotId].indexOf(item);
        if (idx !== -1) {
          currentSelections[slotId].splice(idx, 1);
        } else {
          currentSelections[slotId].push(item);
        }
      } else {
        if (currentSelections[slotId] === item) {
          delete currentSelections[slotId];
        } else {
          currentSelections[slotId] = item;
        }
      }
      updateSlotHighlights();
    }
    updateFinalPromptText(true);
  };

  chip.ondblclick = (e) => {
    e.stopPropagation();
    const oldEn = parsed.en.toLowerCase();
    const newRaw = prompt(t("editTagPrompt"), item);
    if (!newRaw || !newRaw.trim()) return;
    const clean = newRaw.trim();
    
    const list = slot[zoneType];
    const idx = list.indexOf(item);
    if (idx !== -1) list[idx] = clean;

    const slotId = slot.id;
    if (slot.multi) {
      if (Array.isArray(currentSelections[slotId])) {
        const selIdx = currentSelections[slotId].indexOf(item);
        if (selIdx !== -1) currentSelections[slotId][selIdx] = clean;
      }
    } else {
      if (currentSelections[slotId] === item) currentSelections[slotId] = clean;
    }

    legacyTagMap[oldEn] = clean;

    saveConfig();
    renderSlots();
    updateFinalPromptText(true);
  };

  chip.ondragstart = () => { draggedData = { sIdx, zoneType, item, fromGlobal: false }; };

  chip.oncontextmenu = (e) => {
    e.preventDefault();
    if (confirm(t("confirmDelSlotTag", parsed.en))) {
      slot[zoneType] = slot[zoneType].filter(t => t !== item);
      const slotId = slot.id;
      if (slot.multi && Array.isArray(currentSelections[slotId])) {
        currentSelections[slotId] = currentSelections[slotId].filter(t => t !== item);
      } else if (currentSelections[slotId] === item) {
        delete currentSelections[slotId];
      }
      saveConfig();
      renderSlots();
      updateFinalPromptText(true);
    }
  };

  return chip;
}

function handleDrop(e, targetSlotIdx, targetZone) {
  e.preventDefault();
  if (!draggedData) return;
  
  if (draggedData.fromGlobal) {
    const { item, gIdx } = draggedData;
    globalBasket.splice(gIdx, 1);
    if (!slotsConfig[targetSlotIdx][targetZone].includes(item)) slotsConfig[targetSlotIdx][targetZone].push(item);
    draggedData = null;
    saveConfig();
    renderSlots();
    renderGlobalBasket();
    return;
  }

  const { sIdx, zoneType, item } = draggedData;
  draggedData = null;
  if (sIdx === targetSlotIdx && zoneType === targetZone) return;

  slotsConfig[sIdx][zoneType] = slotsConfig[sIdx][zoneType].filter(t => t !== item);
  if (!slotsConfig[targetSlotIdx][targetZone].includes(item)) {
    slotsConfig[targetSlotIdx][targetZone].push(item);
  }

  const targetSlot = slotsConfig[targetSlotIdx];
  const slotId = targetSlot.id;
  if (targetZone === "basket") {
    if (targetSlot.multi && Array.isArray(currentSelections[slotId])) {
      currentSelections[slotId] = currentSelections[slotId].filter(t => t !== item);
    } else if (currentSelections[slotId] === item) {
      delete currentSelections[slotId];
    }
    updateSlotHighlights();
  }

  saveConfig();
  renderSlots();
  updateFinalPromptText(true);
}

function handleGlobalDrop(e) {
  e.preventDefault();
  if (!draggedData || draggedData.fromGlobal) return;
  const { sIdx, zoneType, item } = draggedData;
  draggedData = null;
  
  const slot = slotsConfig[sIdx];
  slot[zoneType] = slot[zoneType].filter(t => t !== item);
  const slotId = slot.id;
  if (slot.multi && Array.isArray(currentSelections[slotId])) {
    currentSelections[slotId] = currentSelections[slotId].filter(t => t !== item);
  } else if (currentSelections[slotId] === item) {
    delete currentSelections[slotId];
  }
  updateSlotHighlights();

  if (!globalBasket.includes(item)) globalBasket.push(item);
  saveConfig();
  renderSlots();
  renderGlobalBasket();
  updateFinalPromptText(true);
}

function addNewSlot() {
  const title = prompt(t("newSlotPrompt"), t("newSlotDefault"));
  if (!title || !title.trim()) return;
  const newId = "slot_" + Date.now();
  slotsConfig.push({ id: newId, title: title.trim(), active: [], basket: [], multi: false });
  saveConfig();
  renderSlots();
}

function deleteSlot(sIdx) {
  const slot = slotsConfig[sIdx];
  if (!confirm(t("confirmDelSlot", slot.title))) return;
  
  const allTags = [...slot.active, ...slot.basket];
  allTags.forEach(t => { if (!globalBasket.includes(t)) globalBasket.push(t); });
  if (currentSelections[slot.id]) delete currentSelections[slot.id];
  
  slotsConfig.splice(sIdx, 1);
  saveConfig();
  renderSlots();
  renderGlobalBasket();
  updateFinalPromptText(true);
}

function addCustomTag(sIdx) {
  const raw = prompt(t("newTagPrompt"));
  if (!raw || !raw.trim()) return;
  const clean = raw.trim();
  const slot = slotsConfig[sIdx];
  if (!slot.active.includes(clean)) {
    slot.active.push(clean);
    const en = parseItem(clean).en.toLowerCase();
    legacyTagMap[en] = clean;
  }
  
  if (slot.multi) {
    if (!currentSelections[slot.id]) currentSelections[slot.id] = [];
    if (!currentSelections[slot.id].includes(clean)) currentSelections[slot.id].push(clean);
  } else {
    currentSelections[slot.id] = clean;
  }

  saveConfig();
  renderSlots();
  updateFinalPromptText(true);
}

function updateSlotHighlights() {
  document.querySelectorAll(".tag-chip").forEach(chip => {
    const slotId = chip.dataset.slotId;
    const item = chip.dataset.item;
    const slot = slotsConfig.find(s => s.id === slotId);
    
    let isSelected = false;
    if (slot && slot.multi) {
      if (Array.isArray(currentSelections[slotId]) && currentSelections[slotId].includes(item)) {
        isSelected = true;
      }
    } else {
      if (slotId && currentSelections[slotId] === item) {
        isSelected = true;
      }
    }

    if (isSelected) {
      chip.classList.add("selected");
    } else {
      chip.classList.remove("selected");
    }
  });
}

async function updateFinalPromptText(autoSave = true) {
  const orderedParts = [];
  slotsConfig.forEach(slot => {
    const val = currentSelections[slot.id];
    if (slot.multi && Array.isArray(val)) {
      val.forEach(item => {
        const parsed = parseItem(item);
        if (parsed.en) orderedParts.push(parsed.en);
      });
    } else if (typeof val === 'string' && val.trim()) {
      const parsed = parseItem(val);
      if (parsed.en) orderedParts.push(parsed.en);
    }
  });
  const result = orderedParts.join(", ");
  document.getElementById("finalPrompt").value = result;

  if (autoSave && currentIndex >= 0 && files[currentIndex]) {
    const fileObj = files[currentIndex];
    await fetch("/api/caption", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ folder: currentFolder, name: fileObj.name, caption: result })
    });
    fileObj.has_txt = result.length > 0;
    renderFileList();
    const ind = document.getElementById("saveIndicator");
    ind.textContent = t("savedBadge");
    setTimeout(() => { ind.textContent = ""; }, 1200);
  }
}

async function saveConfig() {
  if (!currentFolder) return;
  await fetch("/api/config", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ folder: currentFolder, config: { slots: slotsConfig, global_basket: globalBasket } })
  });
}

async function applyFixedToAll() {
  if (!currentFolder || files.length === 0) return alert(t("alertPickFolder"));
  if (!confirm(t("confirmApplyAll", files.length))) return;

  setStatus(t("applyingAll"));
  for (let i = 0; i < files.length; i++) {
    const f = files[i];
    const res = await fetch(`/api/caption?folder=${encodeURIComponent(currentFolder)}&name=${encodeURIComponent(f.name)}`);
    const data = await res.json();
    
    const tempSel = {};
    const caption = data.caption || "";
    slotsConfig.forEach(slot => {
      const allItems = [...slot.active, ...slot.basket];
      if (slot.multi) {
        const matched = [];
        allItems.forEach(item => {
          const en = parseItem(item).en;
          const regex = new RegExp(`(^|,\\s*)${escapeRegExp(en)}(\\s*,|$)`, 'i');
          if (regex.test(caption)) matched.push(item);
        });
        if (matched.length > 0) tempSel[slot.id] = matched;
      } else {
        for (const item of allItems) {
          const en = parseItem(item).en;
          const regex = new RegExp(`(^|,\\s*)${escapeRegExp(en)}(\\s*,|$)`, 'i');
          if (regex.test(caption)) { tempSel[slot.id] = item; break; }
        }
      }
    });

    Object.keys(currentSelections).forEach(id => { tempSel[id] = currentSelections[id]; });
    
    const parts = [];
    slotsConfig.forEach(slot => {
      const val = tempSel[slot.id];
      if (slot.multi && Array.isArray(val)) {
        val.forEach(item => {
          const parsed = parseItem(item);
          if (parsed.en) parts.push(parsed.en);
        });
      } else if (typeof val === 'string' && val.trim()) {
        const parsed = parseItem(val);
        if (parsed.en) parts.push(parsed.en);
      }
    });
    
    const newCap = parts.join(", ");
    await fetch("/api/caption", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ folder: currentFolder, name: f.name, caption: newCap })
    });
    f.has_txt = newCap.length > 0;
  }
  renderFileList();
  selectImage(currentIndex);
  setStatus(t("applyAllDone"));
}

async function openRenameModal() {
  if (!currentFolder || files.length === 0) return alert(t("alertPickFolder"));
  const prefixInput = prompt(t("renamePrompt"), "dataset");
  if (!prefixInput || !prefixInput.trim()) return;
  const prefix = prefixInput.trim();

  if (!confirm(t("confirmRename", prefix, files.length))) return;

  setStatus(t("renamingProgress", prefix, files.length));
  const res = await fetch("/api/rename", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ folder: currentFolder, prefix: prefix })
  });
  const data = await res.json();
  if (data.error) return setStatus(data.error, true);

  files = data.files || [];
  currentIndex = files.length > 0 ? 0 : -1;
  renderFileList();
  if (files.length > 0) {
    await selectImage(0);
  } else {
    document.getElementById("previewImg").src = "";
    document.getElementById("finalPrompt").value = "";
  }
  setStatus(t("renameDone", prefix, files.length));
}

async function aiPrefillCurrent() {
  if (currentIndex < 0) return;
  const model = document.getElementById("ollamaModel").value.trim();
  const fileObj = files[currentIndex];
  setStatus(t("aiRequesting", model));

  const res = await fetch("/api/ai_prefill", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ folder: currentFolder, name: fileObj.name, model: model, slots: slotsConfig })
  });
  const data = await res.json();
  if (data.error) return setStatus(data.error, true);

  const matchedCount = Object.keys(data.selections || {}).length;
  if (matchedCount === 0) {
    return setStatus(t("aiNoMatch"), true);
  }

  Object.entries(data.selections).forEach(([slotId, tag]) => {
    if (tag) {
      const slot = slotsConfig.find(s => s.id === slotId);
      if (slot && slot.multi) {
        if (!currentSelections[slotId]) currentSelections[slotId] = [];
        if (!currentSelections[slotId].includes(tag)) currentSelections[slotId].push(tag);
      } else {
        currentSelections[slotId] = tag;
      }
    }
  });
  updateSlotHighlights();
  await updateFinalPromptText(true);
  setStatus(t("aiMatchedCount", matchedCount));
}

async function aiPrefillAll() {
  if (!currentFolder || files.length === 0) return alert(t("alertPickFolder"));
  const model = document.getElementById("ollamaModel").value.trim();
  if (!confirm(t("confirmAiAll", model, files.length))) return;

  stopBatchFlag = false;
  for (let i = 0; i < files.length; i++) {
    if (stopBatchFlag) break;
    const f = files[i];
    setStatus(t("aiBatchProgress", i + 1, files.length, f.name));
    
    await selectImage(i);

    const res = await fetch("/api/ai_prefill", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ folder: currentFolder, name: f.name, model: model, slots: slotsConfig })
    });
    const data = await res.json();
    if (data.error) {
      setStatus(t("aiBatchError", f.name, data.error), true);
      return;
    }

    Object.entries(data.selections || {}).forEach(([slotId, tag]) => {
      if (tag) {
        const slot = slotsConfig.find(s => s.id === slotId);
        if (slot && slot.multi) {
          if (!currentSelections[slotId]) currentSelections[slotId] = [];
          if (!currentSelections[slotId].includes(tag)) currentSelections[slotId].push(tag);
        } else {
          currentSelections[slotId] = tag;
        }
      }
    });
    updateSlotHighlights();
    await updateFinalPromptText(true);
  }
  setStatus(t("aiBatchDone", files.length));
}

document.addEventListener("keydown", (e) => {
  if (document.activeElement.tagName === "INPUT" || document.activeElement.tagName === "TEXTAREA") return;
  if (e.key === "ArrowDown") { e.preventDefault(); selectImage(currentIndex + 1); }
  else if (e.key === "ArrowUp") { e.preventDefault(); selectImage(currentIndex - 1); }
});

applyStaticI18N();
</script>
</body>
</html>
"""

class TaggerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass

    def _send_json(self, obj, status=200):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path == '/':
            html_bytes = HTML_PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(html_bytes)))
            self.end_headers()
            self.wfile.write(html_bytes)

        elif parsed.path == '/api/image':
            folder = params.get('folder', [''])[0]
            name = params.get('name', [''])[0]
            img_path = os.path.join(folder, name)
            if os.path.isfile(img_path):
                ext = os.path.splitext(name)[1].lower()
                mime = 'image/png' if ext == '.png' else 'image/jpeg'
                with open(img_path, 'rb') as f: data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', mime)
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else: self.send_error(404)

        elif parsed.path == '/api/caption':
            folder = params.get('folder', [''])[0]
            name = params.get('name', [''])[0]
            txt_path = os.path.join(folder, os.path.splitext(name)[0] + '.txt')
            caption = ""
            if os.path.isfile(txt_path):
                with open(txt_path, 'r', encoding='utf-8') as f: caption = f.read().strip()
            self._send_json({"caption": caption})

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length).decode('utf-8')) if length > 0 else {}

        if self.path == '/api/browse':
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            folder_path = filedialog.askdirectory(title="Select image dataset folder")
            root.destroy()
            self._send_json({"folder": folder_path})

        elif self.path == '/api/load':
            folder = body.get('folder', '')
            if not os.path.isdir(folder): return self._send_json({"error": "Folder does not exist."})
            config_path = os.path.join(folder, '_tagger_config.json')
            if os.path.isfile(config_path):
                with open(config_path, 'r', encoding='utf-8') as f: 
                    saved_data = json.load(f)
                    if isinstance(saved_data, list):
                        config = {"slots": saved_data, "global_basket": []}
                    else:
                        config = saved_data
            else:
                config = {"slots": DEFAULT_SLOTS, "global_basket": []}
                with open(config_path, 'w', encoding='utf-8') as f: json.dump(config, f, ensure_ascii=False, indent=2)

            files = []
            for fname in sorted(os.listdir(folder)):
                ext = os.path.splitext(fname)[1].lower()
                if ext in IMAGE_EXTS:
                    txt_path = os.path.join(folder, os.path.splitext(fname)[0] + '.txt')
                    has_txt = os.path.isfile(txt_path) and os.path.getsize(txt_path) > 0
                    files.append({"name": fname, "has_txt": has_txt})
            self._send_json({"files": files, "config": config})

        elif self.path == '/api/caption':
            folder = body.get('folder', '')
            name = body.get('name', '')
            caption = body.get('caption', '')
            txt_path = os.path.join(folder, os.path.splitext(name)[0] + '.txt')
            with open(txt_path, 'w', encoding='utf-8') as f: f.write(caption)
            self._send_json({"ok": True})

        elif self.path == '/api/config':
            folder = body.get('folder', '')
            config = body.get('config', {})
            config_path = os.path.join(folder, '_tagger_config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self._send_json({"ok": True})

        elif self.path == '/api/delete_file':
            folder = body.get('folder', '')
            name = body.get('name', '')
            img_path = os.path.join(folder, name)
            txt_path = os.path.join(folder, os.path.splitext(name)[0] + '.txt')
            try:
                if os.path.isfile(img_path): os.remove(img_path)
                if os.path.isfile(txt_path): os.remove(txt_path)
                self._send_json({"ok": True})
            except Exception as e:
                self._send_json({"error": f"Delete failed: {e}"})

        elif self.path == '/api/rename':
            folder = body.get('folder', '')
            prefix = body.get('prefix', '').strip()
            if not os.path.isdir(folder):
                return self._send_json({"error": "Invalid folder path."})
            if not prefix:
                return self._send_json({"error": "Prefix cannot be empty."})

            img_names = sorted([f for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in IMAGE_EXTS])
            staged_items = []

            try:
                for idx, old_img in enumerate(img_names, 1):
                    ext = os.path.splitext(old_img)[1].lower()
                    old_base = os.path.splitext(old_img)[0]
                    old_img_path = os.path.join(folder, old_img)
                    old_txt_path = os.path.join(folder, old_base + '.txt')
                    has_old_txt = os.path.isfile(old_txt_path)

                    tmp_base = f"__xdtag_tmp_{idx}_{prefix}"
                    tmp_img_path = os.path.join(folder, tmp_base + ext)
                    tmp_txt_path = os.path.join(folder, tmp_base + '.txt')

                    os.rename(old_img_path, tmp_img_path)
                    if has_old_txt:
                        os.rename(old_txt_path, tmp_txt_path)

                    final_base = f"{prefix}{idx}"
                    staged_items.append({
                        "tmp_img": tmp_img_path,
                        "tmp_txt": tmp_txt_path if has_old_txt else None,
                        "final_img": os.path.join(folder, final_base + ext),
                        "final_txt": os.path.join(folder, final_base + '.txt'),
                        "final_img_name": final_base + ext
                    })

                new_files = []
                for item in staged_items:
                    os.rename(item["tmp_img"], item["final_img"])
                    if item["tmp_txt"] and os.path.isfile(item["tmp_txt"]):
                        os.rename(item["tmp_txt"], item["final_txt"])

                    has_txt = os.path.isfile(item["final_txt"]) and os.path.getsize(item["final_txt"]) > 0
                    new_files.append({"name": item["final_img_name"], "has_txt": has_txt})

                self._send_json({"files": new_files})
            except Exception as e:
                self._send_json({"error": f"Rename failed: {e}"})

        elif self.path == '/api/ai_prefill':
            folder = body.get('folder', '')
            name = body.get('name', '')
            model = body.get('model', 'qwen2.5vl:7b')
            slots = body.get('slots', [])
            img_path = os.path.join(folder, name)

            try:
                with open(img_path, 'rb') as f:
                    img_b64 = base64.b64encode(f.read()).decode('utf-8')

                rules = []
                for s in slots:
                    if not s["active"]: continue
                    opts = " | ".join([f'"{t.split("|")[0].strip()}"' for t in s["active"]])
                    if s.get("multi"):
                        rules.append(f'- Key "{s["id"]}" ({s["title"]}): pick ANY matching from [{opts}] or empty array if none.')
                    else:
                        rules.append(f'- Key "{s["id"]}" ({s["title"]}): pick ONE from [{opts}] or "" if none fits.')

                prompt = (
                    "Look at this character portrait. For each Key, pick matching English phrases from its allowed list based on its single/multi rule. "
                    "Output ONLY a raw JSON object where keys are exact slot IDs and values are strings (for single) or arrays of strings (for multi).\n\n"
                    + "\n".join(rules)
                )

                payload = json.dumps({
                    "model": model, "prompt": prompt, "images": [img_b64],
                    "format": "json", "stream": False, "options": {"temperature": 0.1}
                }).encode('utf-8')

                req = urllib.request.Request(
                    "http://127.0.0.1:11434/api/generate",
                    data=payload,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=180) as resp:
                    res_data = json.loads(resp.read().decode('utf-8'))
                    raw_text = res_data.get("response", "{}")
                    raw_selections = json.loads(raw_text)
                    
                    selections = {}
                    for s in slots:
                        s_id = s["id"]
                        val = raw_selections.get(s_id, raw_selections.get(s["title"], ""))
                        if s.get("multi"):
                            if isinstance(val, list):
                                matched_arr = []
                                for v in val:
                                    v_clean = re.sub(r'^[\s,"\'\.]+|[\s,"\'\.]+$', '', str(v)).lower()
                                    for item in s["active"]:
                                        item_en = item.split('|')[0].strip().lower()
                                        if item_en == v_clean or (len(v_clean) > 3 and v_clean in item_en):
                                            matched_arr.append(item)
                                            break
                                if matched_arr: selections[s_id] = matched_arr[0]
                        else:
                            ai_val = str(val).strip()
                            ai_clean = re.sub(r'^[\s,"\'\.]+|[\s,"\'\.]+$', '', ai_val).lower()
                            if ai_clean:
                                for item in s["active"]:
                                    item_en = item.split('|')[0].strip().lower()
                                    if item_en == ai_clean or (len(ai_clean) > 4 and (ai_clean in item_en or item_en in ai_clean)):
                                        selections[s_id] = item
                                        break

                    self._send_json({"selections": selections})
            except Exception as e:
                self._send_json({"error": f"Ollama call failed: {e}"})

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', PORT), TaggerHandler)
    print(f"xd_char_tagger running at: http://127.0.0.1:{PORT}")
    threading.Timer(0.8, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}")).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")