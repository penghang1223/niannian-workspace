/**
 * 调用次数限制管理器
 * 
 * 功能：
 * - 记录每个用户的调用次数
 * - 支持设置每日/每小时限制
 * - 自动重置计数
 * - 支持手动配置
 */

const fs = require('fs');
const path = require('path');

class RateLimitManager {
    constructor() {
        this.configPath = path.join(__dirname, 'config', 'rate_limits.json');
        this.usagePath = path.join(__dirname, 'config', 'usage_stats.json');
        this.limits = {};
        this.usage = {};
        this._loadConfig();
        this._loadUsage();
    }
    
    /**
     * 加载配置
     * @private
     */
    _loadConfig() {
        try {
            if (fs.existsSync(this.configPath)) {
                this.limits = JSON.parse(fs.readFileSync(this.configPath, 'utf8'));
            } else {
                // 默认配置
                this.limits = {
                    default: {
                        daily: 100,      // 每日限制
                        hourly: 20,      // 每小时限制
                        perMinute: 5     // 每分钟限制
                    },
                    admin: {
                        daily: 1000,
                        hourly: 100,
                        perMinute: 20
                    },
                    beta_user: {
                        daily: 200,
                        hourly: 30,
                        perMinute: 8
                    },
                    user: {
                        daily: 50,
                        hourly: 10,
                        perMinute: 3
                    }
                };
                this._saveConfig();
            }
        } catch (error) {
            console.error(`[RateLimit] 加载配置失败：${error.message}`);
        }
    }
    
    /**
     * 加载使用统计
     * @private
     */
    _loadUsage() {
        try {
            if (fs.existsSync(this.usagePath)) {
                this.usage = JSON.parse(fs.readFileSync(this.usagePath, 'utf8'));
            } else {
                this.usage = {};
                this._saveUsage();
            }
        } catch (error) {
            console.error(`[RateLimit] 加载使用统计失败：${error.message}`);
        }
    }
    
    /**
     * 保存配置
     * @private
     */
    _saveConfig() {
        try {
            fs.writeFileSync(this.configPath, JSON.stringify(this.limits, null, 2));
        } catch (error) {
            console.error(`[RateLimit] 保存配置失败：${error.message}`);
        }
    }
    
    /**
     * 保存使用统计
     * @private
     */
    _saveUsage() {
        try {
            fs.writeFileSync(this.usagePath, JSON.stringify(this.usage, null, 2));
        } catch (error) {
            console.error(`[RateLimit] 保存使用统计失败：${error.message}`);
        }
    }
    
    /**
     * 获取用户限制配置
     * @param {string} userId 
     * @returns {object}
     */
    getUserLimit(userId) {
        // 检查是否有用户自定义限制
        if (this.limits.users && this.limits.users[userId]) {
            return this.limits.users[userId];
        }
        
        // 返回角色默认限制
        const role = this._getUserRole(userId);
        return this.limits[role] || this.limits.default;
    }
    
    /**
     * 获取用户角色
     * @private
     */
    _getUserRole(userId) {
        // 从多角色配置中获取用户角色
        try {
            const configPath = path.join(__dirname, 'config', 'multi_role_config.json');
            if (fs.existsSync(configPath)) {
                const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
                const userConfig = config.users?.[userId];
                if (userConfig) {
                    return userConfig.profile?.role || userConfig.user_profile?.role || 'user';
                }
            }
        } catch (error) {
            // 忽略错误
        }
        return 'user';
    }
    
    /**
     * 检查是否超过限制
     * @param {string} userId 
     * @returns {object} { allowed: boolean, reason?: string, resetAt?: number }
     */
    checkLimit(userId) {
        const limit = this.getUserLimit(userId);
        const usage = this.getUserUsage(userId);
        const now = Date.now();
        
        // 检查每分钟限制
        const minuteAgo = now - 60 * 1000;
        const minuteCount = usage.requests?.filter(t => t > minuteAgo).length || 0;
        if (minuteCount >= limit.perMinute) {
            return {
                allowed: false,
                reason: '超过每分钟限制',
                limit: limit.perMinute,
                current: minuteCount,
                resetAt: minuteAgo + 60 * 1000
            };
        }
        
        // 检查每小时限制
        const hourAgo = now - 60 * 60 * 1000;
        const hourCount = usage.requests?.filter(t => t > hourAgo).length || 0;
        if (hourCount >= limit.hourly) {
            return {
                allowed: false,
                reason: '超过每小时限制',
                limit: limit.hourly,
                current: hourCount,
                resetAt: hourAgo + 60 * 60 * 1000
            };
        }
        
        // 检查每日限制
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const dayCount = usage.requests?.filter(t => t > today.getTime()).length || 0;
        if (dayCount >= limit.daily) {
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);
            return {
                allowed: false,
                reason: '超过每日限制',
                limit: limit.daily,
                current: dayCount,
                resetAt: tomorrow.getTime()
            };
        }
        
        return {
            allowed: true,
            limit,
            usage: {
                perMinute: minuteCount,
                hourly: hourCount,
                daily: dayCount
            }
        };
    }
    
    /**
     * 记录调用
     * @param {string} userId 
     */
    recordUsage(userId) {
        if (!this.usage[userId]) {
            this.usage[userId] = {
                requests: [],
                totalRequests: 0,
                lastRequest: null
            };
        }
        
        const now = Date.now();
        this.usage[userId].requests.push(now);
        this.usage[userId].totalRequests++;
        this.usage[userId].lastRequest = now;
        
        // 清理旧记录（保留 24 小时）
        const dayAgo = now - 24 * 60 * 60 * 1000;
        this.usage[userId].requests = this.usage[userId].requests.filter(t => t > dayAgo);
        
        this._saveUsage();
    }
    
    /**
     * 获取用户使用统计
     * @param {string} userId 
     * @returns {object}
     */
    getUserUsage(userId) {
        const usage = this.usage[userId] || { requests: [], totalRequests: 0 };
        const now = Date.now();
        
        const minuteAgo = now - 60 * 1000;
        const hourAgo = now - 60 * 60 * 1000;
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        return {
            perMinute: usage.requests.filter(t => t > minuteAgo).length,
            hourly: usage.requests.filter(t => t > hourAgo).length,
            daily: usage.requests.filter(t => t > today.getTime()).length,
            totalRequests: usage.totalRequests,
            lastRequest: usage.lastRequest
        };
    }
    
    /**
     * 设置用户限制
     * @param {string} userId 
     * @param {object} limits 
     */
    setUserLimit(userId, limits) {
        if (!this.limits.users) {
            this.limits.users = {};
        }
        
        this.limits.users[userId] = {
            ...this.limits.default,
            ...limits
        };
        
        this._saveConfig();
    }
    
    /**
     * 重置用户限制
     * @param {string} userId 
     */
    resetUserLimit(userId) {
        if (this.limits.users && this.limits.users[userId]) {
            delete this.limits.users[userId];
            this._saveConfig();
        }
    }
    
    /**
     * 重置用户使用统计
     * @param {string} userId 
     */
    resetUserUsage(userId) {
        if (this.usage[userId]) {
            this.usage[userId] = {
                requests: [],
                totalRequests: this.usage[userId].totalRequests,
                lastRequest: null
            };
            this._saveUsage();
        }
    }
    
    /**
     * 获取所有限制配置
     * @returns {object}
     */
    getAllLimits() {
        return this.limits;
    }
    
    /**
     * 获取所有用户使用统计
     * @returns {object}
     */
    getAllUsage() {
        const stats = {};
        Object.keys(this.usage).forEach(userId => {
            stats[userId] = this.getUserUsage(userId);
        });
        return stats;
    }
}

// 导出单例
const rateLimitManager = new RateLimitManager();

module.exports = {
    RateLimitManager,
    rateLimitManager
};
