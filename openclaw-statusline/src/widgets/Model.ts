/**
 * Model Information Widget for OpenClaw Status Line
 * Shows the current model being used
 */

export class ModelWidget {
  private currentModel: string = '';
  private modelProvider: string = '';

  constructor() {
    this.fetchModelInfo();
  }

  async getValue(): Promise<{ label: string; value: string; color: string }> {
    // Refresh model info
    this.fetchModelInfo();
    
    const modelDisplay = this.currentModel || 'unknown';
    
    return {
      label: 'Model',
      value: modelDisplay,
      color: '#800080' // Purple
    };
  }

  private fetchModelInfo(): void {
    try {
      // In a real implementation, this would get the current model from OpenClaw
      // For now, we'll try to determine it from environment or default settings
      this.currentModel = process.env.MODEL || process.env.OPENAI_MODEL || 'qwen3-coder-plus';
      this.modelProvider = this.extractProvider(this.currentModel);
    } catch (error: any) {
      this.currentModel = 'unknown';
      this.modelProvider = 'unknown';
    }
  }

  private extractProvider(modelName: string): string {
    if (modelName.includes('gpt')) {
      return 'openai';
    } else if (modelName.includes('claude')) {
      return 'anthropic';
    } else if (modelName.includes('llama') || modelName.includes('meta')) {
      return 'meta';
    } else if (modelName.includes('qwen') || modelName.includes('bailian')) {
      return 'bailian';
    } else {
      return 'unknown';
    }
  }

  // Method to update model info externally
  updateModelInfo(modelName: string): void {
    this.currentModel = modelName;
    this.modelProvider = this.extractProvider(modelName);
  }

  // Get current model info
  getModelInfo(): { name: string; provider: string } {
    return {
      name: this.currentModel,
      provider: this.modelProvider
    };
  }
}