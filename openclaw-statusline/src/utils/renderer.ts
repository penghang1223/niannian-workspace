/**
 * Renderer for OpenClaw Status Line
 */

import { Config } from './config';

export class Renderer {
  private config: Config;

  constructor(config: Config) {
    this.config = config;
  }

  render(widgets: Array<{ label: string; value: string; color: string }>): string {
    const separator = this.config.get('separator', ' | ');
    const position = this.config.get('position', 'bottom');
    
    // Format each widget with color and styling
    const formattedWidgets = widgets.map(widget => {
      const color = widget.color || this.config.get(`colors.${widget.label.toLowerCase()}`, '#ffffff');
      return this.applyColor(`${widget.label}: ${widget.value}`, color);
    });

    const statusLine = formattedWidgets.join(separator);
    
    // Depending on position, we might format differently
    if (position === 'top') {
      return `┌─${'─'.repeat(process.stdout.columns - 4)}─┐\n│ ${statusLine} │\n└─${'─'.repeat(process.stdout.columns - 4)}─┘`;
    } else {
      // Bottom position - just return the status line
      return statusLine;
    }
  }

  private applyColor(text: string, color: string): string {
    // Simple ANSI color codes for now, could be extended with proper color library
    const colorMap: { [key: string]: string } = {
      '#00ff00': '\x1b[32m', // Green
      '#ffff00': '\x1b[33m', // Yellow
      '#ff00ff': '\x1b[35m', // Magenta
      '#00ffff': '\x1b[36m', // Cyan
      '#ffa500': '\x1b[38;5;208m', // Orange
      '#ff0000': '\x1b[31m', // Red
      '#800080': '\x1b[38;5;93m', // Purple
      '#ffffff': '\x1b[37m'  // White
    };

    const resetCode = '\x1b[0m';
    const colorCode = colorMap[color] || '\x1b[37m'; // Default to white
    
    return `${colorCode}${text}${resetCode}`;
  }
}