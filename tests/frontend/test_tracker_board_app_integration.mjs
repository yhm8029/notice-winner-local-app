import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appPath = path.resolve(__dirname, "../../frontend/app-runtime-body.js");

function readAppSource() {
  return fs.readFileSync(appPath, "utf8");
}

test("renderTrackerBoard is a thin wrapper around the tracker render controller", () => {
  const source = readAppSource();
  const start = source.indexOf("function renderTrackerBoard(entries) {");
  const end = source.indexOf("function renderTrackerBoardFallback(entries) {", start);
  const block = source.slice(start, end);

  assert.ok(block.length > 0, "renderTrackerBoard wrapper should exist");
  assert.match(block, /getTrackerRenderController/);
  assert.match(block, /controller\?\.renderTrackerBoard/);
  assert.match(block, /renderTrackerBoardFallback/);
  assert.doesNotMatch(block, /buildTrackerBoardEmptyStateView/);
  assert.doesNotMatch(block, /buildTrackerBoardMarkup/);
  assert.doesNotMatch(block, /buildTrackerBoardMarkupFallback/);
  assert.doesNotMatch(block, /TRACKER_BOARD_COLUMNS\.map\(/);
  assert.doesNotMatch(block, /renderTrackerBoardHeaderCell/);
  assert.doesNotMatch(block, /renderTrackerBoardCell/);
  assert.doesNotMatch(block, /renderTrackerBoardEditingCell/);
  assert.doesNotMatch(block, /dom\.trackerBoard\.innerHTML\s*=\s*`/);
});

test("tracker board fallback wrappers delegate to the fallback runtime", () => {
  const source = readAppSource();

  const markupStart = source.indexOf("function buildTrackerBoardMarkupFallback(");
  const markupEnd = source.indexOf("function renderTrackerBoard(entries) {", markupStart);
  const markupBlock = source.slice(markupStart, markupEnd);
  assert.ok(markupBlock.length > 0, "buildTrackerBoardMarkupFallback wrapper should exist");
  assert.match(markupBlock, /getTrackerRenderFallbackRuntime/);
  assert.match(markupBlock, /buildTrackerBoardMarkupFallback/);
  assert.doesNotMatch(markupBlock, /TRACKER_BOARD_COLUMNS\.map\(|tracker-board-table|data-board-sort-field|data-board-edit-trigger/);

  const renderStart = source.indexOf("function renderTrackerBoardFallback(entries) {");
  const renderEnd = source.indexOf("function toggleTrackerBoardBlankPriority(", renderStart);
  const renderBlock = source.slice(renderStart, renderEnd);
  assert.ok(renderBlock.length > 0, "renderTrackerBoardFallback wrapper should exist");
  assert.match(renderBlock, /getTrackerRenderFallbackRuntime/);
  assert.match(renderBlock, /renderTrackerBoardFallback/);
  assert.doesNotMatch(renderBlock, /data-board-sort-field|data-board-edit-trigger|tracker-board-table|tracker-board-edit-input/);
});

test("tracker board helper wrappers defer header and blank-priority fallbacks to the shared runtime", () => {
  const source = readAppSource();

  const headerStart = source.indexOf("function renderTrackerBoardHeaderCell(column) {");
  const headerEnd = source.indexOf("function isTrackerBoardBlankValue(value) {", headerStart);
  const headerBlock = source.slice(headerStart, headerEnd);
  assert.ok(headerBlock.length > 0, "renderTrackerBoardHeaderCell wrapper should exist");
  assert.match(headerBlock, /getTrackerRenderFallbackHelpers/);
  assert.match(headerBlock, /APP_SUPPORT\.renderTrackerBoardHeaderCellBridge/);
  assert.match(headerBlock, /TRACKER_BOARD_RUNTIME/);
  assert.doesNotMatch(headerBlock, /tracker-board-sort-trigger|data-board-sort-field/);

  const cellStart = source.indexOf("function renderTrackerBoardCell({ entry, column, displayNo }) {");
  const cellEnd = source.indexOf("function renderTrackerBoardEditingCell({ entry, fieldName, label, value, saving, errorMessage }) {", cellStart);
  const cellBlock = source.slice(cellStart, cellEnd);
  assert.ok(cellBlock.length > 0, "renderTrackerBoardCell wrapper should exist");
  assert.match(cellBlock, /APP_SUPPORT\.renderTrackerBoardCellBridge/);
  assert.match(cellBlock, /TRACKER_BOARD_RUNTIME/);
  assert.match(cellBlock, /getTrackerRenderFallbackHelpers/);
  assert.match(cellBlock, /buildTrackerBoardCellMarkupFallback/);
  assert.doesNotMatch(cellBlock, /TRACKER_BOARD_RUNTIME\?\.buildTrackerBoardCellMarkup|TRACKER_BOARD_RUNTIME\?\.renderTrackerBoardCell/);
  assert.doesNotMatch(cellBlock, /tracker-board-edit-trigger|data-board-edit-form/);

  const editingStart = source.indexOf("function renderTrackerBoardEditingCell({ entry, fieldName, label, value, saving, errorMessage }) {");
  const editingEnd = source.indexOf("function beginTrackerBoardEdit(entryId, fieldName) {", editingStart);
  const editingBlock = source.slice(editingStart, editingEnd);
  assert.ok(editingBlock.length > 0, "renderTrackerBoardEditingCell wrapper should exist");
  assert.match(editingBlock, /APP_SUPPORT\.renderTrackerBoardEditingCellBridge/);
  assert.match(editingBlock, /TRACKER_BOARD_RUNTIME/);
  assert.match(editingBlock, /getTrackerRenderFallbackHelpers/);
  assert.match(editingBlock, /buildTrackerBoardEditingCellMarkupFallback/);
  assert.doesNotMatch(editingBlock, /TRACKER_BOARD_RUNTIME\?\.buildTrackerBoardEditingCellMarkup|TRACKER_BOARD_RUNTIME\?\.renderTrackerBoardEditingCell/);
  assert.doesNotMatch(editingBlock, /tracker-board-edit-form|data-board-edit-input/);

  const blankStart = source.indexOf("function isTrackerBoardBlankValue(value) {", headerStart);
  const blankEnd = source.indexOf("function sortTrackerBoardEntriesFallback(entries,", blankStart);
  const blankBlock = source.slice(blankStart, blankEnd);
  assert.ok(blankBlock.length > 0, "isTrackerBoardBlankValue wrapper should exist");
  assert.match(blankBlock, /getTrackerRenderFallbackHelpers/);
  assert.match(blankBlock, /APP_SUPPORT\.isTrackerBoardBlankValueBridge/);
  assert.match(blankBlock, /TRACKER_BOARD_RUNTIME/);
  assert.doesNotMatch(blankBlock, /priorityFields|leftBlank|rightBlank|\.sort\(/);
});
