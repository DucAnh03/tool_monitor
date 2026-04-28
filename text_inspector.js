#!/usr/bin/env node

const fs = require("node:fs");

const STOP_WORDS = new Set([
  "a",
  "an",
  "and",
  "are",
  "as",
  "at",
  "be",
  "by",
  "for",
  "from",
  "in",
  "is",
  "it",
  "of",
  "on",
  "or",
  "that",
  "the",
  "to",
  "with",
]);

function parseArgs(argv) {
  const args = {
    filePath: null,
    text: null,
    top: 5,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (item === "--text") {
      args.text = argv[index + 1] || "";
      index += 1;
    } else if (item === "--top") {
      args.top = Number.parseInt(argv[index + 1], 10);
      index += 1;
    } else if (!args.filePath) {
      args.filePath = item;
    }
  }

  if (!Number.isInteger(args.top) || args.top < 1) {
    args.top = 5;
  }

  return args;
}

function readInput(args) {
  if (args.text !== null) {
    return args.text;
  }

  if (args.filePath) {
    return fs.readFileSync(args.filePath, "utf8");
  }

  return fs.readFileSync(0, "utf8");
}

function inspectText(text, topLimit) {
  const words = text.toLowerCase().match(/[a-z0-9']+/g) || [];
  const sentences = text.split(/[.!?]+/).filter((part) => part.trim().length > 0);
  const lines = text.split(/\r?\n/);
  const frequencies = new Map();

  for (const word of words) {
    if (STOP_WORDS.has(word)) {
      continue;
    }
    frequencies.set(word, (frequencies.get(word) || 0) + 1);
  }

  const topWords = [...frequencies.entries()]
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
    .slice(0, topLimit);

  return {
    characters: text.length,
    lines: text.length === 0 ? 0 : lines.length,
    sentences: sentences.length,
    words: words.length,
    uniqueWords: new Set(words).size,
    topWords,
  };
}

function renderReport(report) {
  const output = [
    "Text Inspector",
    "==============",
    `Characters: ${report.characters}`,
    `Lines: ${report.lines}`,
    `Sentences: ${report.sentences}`,
    `Words: ${report.words}`,
    `Unique words: ${report.uniqueWords}`,
    "",
    "Top Words",
    "---------",
  ];

  if (report.topWords.length === 0) {
    output.push("No words found.");
  } else {
    for (const [word, count] of report.topWords) {
      output.push(`${word.padEnd(16)} ${count}`);
    }
  }

  return output.join("\n");
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const text = readInput(args);
  console.log(renderReport(inspectText(text, args.top)));
}

if (require.main === module) {
  main();
}
