/**
 * 飞书语音发送技能（OpenClaw 集成版）
 * 
 * 所有机器人都可以使用此技能发送语音消息
 * 使用 OpenClaw message 工具，自动路由到正确的聊天
 * 
 * 用法：
 * const voiceSender = require('./skills/feishu-voice-sender');
 * await voiceSender.sendVoice('要说的内容', { voice: 'zh-CN-XiaoxiaoNeural' });
 */

const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const DEFAULT_VOICE = 'zh-CN-XiaoxiaoNeural';

/**
 * 生成语音文件
 * @param {string} text - 要转换的文本
 * @param {string} voice - 音色
 * @returns {Promise<string>} - 生成的 opus 文件路径
 */
async function generateVoice(text, voice = DEFAULT_VOICE) {
  return new Promise((resolve, reject) => {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'voice-'));
    const mp3Path = path.join(tmpDir, 'voice.mp3');
    const opusPath = path.join(tmpDir, 'voice.opus');
    
    // 生成 MP3
    exec(`edge-tts --voice "${voice}" --text "${text.replace(/"/g, '\\"')}" --write-media "${mp3Path}"`, (error) => {
      if (error) {
        reject(new Error(`语音生成失败：${error.message}`));
        return;
      }
      
      // 转换为 OPUS
      exec(`ffmpeg -i "${mp3Path}" -c:a libopus "${opusPath}" -y 2>/dev/null`, (error) => {
        if (error) {
          reject(new Error(`格式转换失败：${error.message}`));
          return;
        }
        
        // 清理 MP3
        fs.unlinkSync(mp3Path);
        
        resolve(opusPath);
      });
    });
  });
}

/**
 * 发送语音消息（通过 OpenClaw message 工具）
 * 
 * @param {string} text - 要说的内容
 * @param {object} options - 选项
 * @param {string} options.voice - 音色（默认：zh-CN-XiaoxiaoNeural）
 * @param {string} options.channel - 渠道（默认：feishu）
 * @param {string} options.message - 附加的文本消息（可选）
 * @returns {Promise<object>} - 发送结果
 */
async function sendVoice(text, options = {}) {
  const {
    voice = DEFAULT_VOICE,
    channel = 'feishu',
    message = ''
  } = options;
  
  console.log(`[FeishuVoice] 生成语音：${text.substring(0, 50)}...`);
  
  try {
    // 生成语音文件
    const opusPath = await generateVoice(text, voice);
    console.log(`[FeishuVoice] 语音文件已生成：${opusPath}`);
    
    // 使用 OpenClaw message 工具发送
    // 注意：这里需要调用 OpenClaw 的 tool 系统
    // 在 agent 代码中，应该这样调用：
    // const result = await tools.message({
    //   action: 'send',
    //   channel: channel,
    //   filePath: opusPath,
    //   mimeType: 'audio/opus',
    //   message: message || text
    // });
    
    // 返回文件路径，由调用者使用 message 工具发送
    return {
      success: true,
      opusPath,
      message: '请使用 OpenClaw message 工具发送此语音文件',
      example: `
        const result = await tools.message({
          action: 'send',
          channel: '${channel}',
          filePath: '${opusPath}',
          mimeType: 'audio/opus',
          message: '${message || text}'
        });
      `
    };
    
  } catch (error) {
    console.error(`[FeishuVoice] 发送失败：${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * 清理临时语音文件
 * @param {string} opusPath - 语音文件路径
 */
function cleanup(opusPath) {
  try {
    if (fs.existsSync(opusPath)) {
      fs.unlinkSync(opusPath);
      // 清理临时目录
      const tmpDir = path.dirname(opusPath);
      if (tmpDir.startsWith(os.tmpdir())) {
        fs.rmdirSync(tmpDir);
      }
    }
  } catch (error) {
    console.error(`[FeishuVoice] 清理失败：${error.message}`);
  }
}

module.exports = {
  sendVoice,
  generateVoice,
  cleanup,
  DEFAULT_VOICE
};
