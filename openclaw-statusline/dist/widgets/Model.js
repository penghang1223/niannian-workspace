"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ModelWidget = void 0;
class ModelWidget {
    constructor() {
        this.currentModel = '';
        this.modelProvider = '';
        this.fetchModelInfo();
    }
    async getValue() {
        this.fetchModelInfo();
        const modelDisplay = this.currentModel || 'unknown';
        return {
            label: 'Model',
            value: modelDisplay,
            color: '#800080'
        };
    }
    fetchModelInfo() {
        try {
            this.currentModel = process.env.MODEL || process.env.OPENAI_MODEL || 'qwen3-coder-plus';
            this.modelProvider = this.extractProvider(this.currentModel);
        }
        catch (error) {
            this.currentModel = 'unknown';
            this.modelProvider = 'unknown';
        }
    }
    extractProvider(modelName) {
        if (modelName.includes('gpt')) {
            return 'openai';
        }
        else if (modelName.includes('claude')) {
            return 'anthropic';
        }
        else if (modelName.includes('llama') || modelName.includes('meta')) {
            return 'meta';
        }
        else if (modelName.includes('qwen') || modelName.includes('bailian')) {
            return 'bailian';
        }
        else {
            return 'unknown';
        }
    }
    updateModelInfo(modelName) {
        this.currentModel = modelName;
        this.modelProvider = this.extractProvider(modelName);
    }
    getModelInfo() {
        return {
            name: this.currentModel,
            provider: this.modelProvider
        };
    }
}
exports.ModelWidget = ModelWidget;
//# sourceMappingURL=Model.js.map