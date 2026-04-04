import { derived, writable } from 'zustand';

// 用户状态管理
export const useAuthStore = writable({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true
});

// 获取存储的 token
export const getStoredToken = () => {
  if (typeof localStorage !== 'undefined') {
    return localStorage.getItem('auth_token');
  }
  return null;
};

// 存储 token
export const setStoredToken = (token) => {
  if (typeof localStorage !== 'undefined') {
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }
};

// 清除认证状态
export const clearAuth = () => {
  setStoredToken(null);
  useAuthStore.setState({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false
  });
};

// 登录
export const login = async (email, password) => {
  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      throw new Error('登录失败');
    }

    const data = await response.json();

    // 存储 token
    setStoredToken(data.token);

    // 更新状态
    useAuthStore.setState({
      user: data.user,
      token: data.token,
      isAuthenticated: true,
      isLoading: false
    });

    return data;
  } catch (error) {
    clearAuth();
    throw error;
  }
};

// 注册
export const register = async (name, email, password) => {
  try {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ name, email, password })
    });

    if (!response.ok) {
      throw new Error('注册失败');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    throw error;
  }
};

// 获取当前用户
export const getCurrentUser = async () => {
  try {
    const token = getStoredToken();
    if (!token) {
      useAuthStore.setState({ isLoading: false });
      return null;
    }

    const response = await fetch('/api/auth/me', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      clearAuth();
      return null;
    }

    const user = await response.json();

    useAuthStore.setState({
      user,
      token,
      isAuthenticated: true,
      isLoading: false
    });

    return user;
  } catch (error) {
    clearAuth();
    useAuthStore.setState({ isLoading: false });
    return null;
  }
};

// 受保护的 API 调用
export const fetchWithAuth = async (url, options = {}) => {
  const token = getStoredToken();

  if (!token) {
    throw new Error('未认证');
  }

  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`
  };

  const response = await fetch(url, {
    ...options,
    headers
  });

  if (response.status === 401) {
    clearAuth();
    throw new Error('认证过期');
  }

  return response;
};

// 检查认证状态
export const checkAuth = async () => {
  const token = getStoredToken();
  if (token) {
    try {
      await getCurrentUser();
    } catch (error) {
      clearAuth();
    }
  } else {
    useAuthStore.setState({ isLoading: false });
  }
};