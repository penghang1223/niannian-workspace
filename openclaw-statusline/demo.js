/**
 * Demo script for OpenClaw Status Line
 * Demonstrates the functionality of the status bar
 */

// Since the main implementation is in TypeScript, this demo shows the concept
// In a real scenario, you'd run the TypeScript version with ts-node

console.log("OpenClaw Status Line - Demo");
console.log("=============================");
console.log();

// Simulate the status line output
function simulateStatusLine() {
  const tokens = Math.floor(Math.random() * 10000) + 5000;
  const hours = Math.floor(Math.random() * 10) + 1;
  const minutes = Math.floor(Math.random() * 60);
  const seconds = Math.floor(Math.random() * 60);
  const project = "openclaw-workspace";
  const cost = (Math.random() * 10).toFixed(6);
  
  // Try to get git branch
  let gitBranch = "";
  try {
    const { execSync } = require('child_process');
    gitBranch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf8' }).trim();
  } catch (e) {
    gitBranch = "main"; // default
  }
  
  const agent = "main (1)";
  const model = "qwen3-coder-plus";

  console.log(`Tokens: ${tokens.toLocaleString()} | Session: ${hours}h ${minutes}m ${seconds}s | Project: ${project} | Cost: $${cost} | Branch: ${gitBranch} | Agent: ${agent} | Model: ${model}`);
}

console.log("Example status line output:");
simulateStatusLine();
console.log();
console.log("The actual implementation uses TypeScript with modular widgets");
console.log("and real-time updates for token usage, session time, and other metrics.");