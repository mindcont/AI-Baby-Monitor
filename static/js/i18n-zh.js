(function () {
    'use strict';

    const translations = {
        'AI Baby Monitor': 'AI 婴儿监控',
        'Navigation': '导航',
        'Dashboard': '仪表盘',
        'Users': '用户管理',
        'Logs': '日志',
        'Shortcuts': '快捷键',
        'Live Alerts': '实时提醒',
        'All systems normal': '系统运行正常',
        'Refresh': '刷新',
        'Clear': '清除',
        'Change Password': '修改密码',
        'Sign Out': '退出登录',
        'System Online': '系统在线',
        'AI-Powered Baby Monitor': 'AI 婴儿监控系统',
        'Advanced real-time monitoring with computer vision, sleep analysis, and intelligent safety alerts': '基于计算机视觉、睡眠分析和智能安全提醒的实时监控',
        'Live Stream Active': '实时视频已开启',
        'AI Processing': 'AI 处理中',
        'Safe Zone OK': '安全区域正常',
        'Detection Rate': '检测率',
        'State': '状态',
        'Room Temp': '室温',
        'Sleep Time': '睡眠时长',
        'Connecting...': '连接中...',
        'Connected': '已连接',
        'Disconnected': '已断开',
        'Protocol:': '协议：',
        'Clients:': '客户端：',
        'FPS:': '帧率：',
        'Quality:': '画质：',
        'Apply': '应用',
        'Pause': '暂停',
        'Resume': '继续',
        'Camera Offline': '摄像头离线',
        'Your streaming access has been disabled by an administrator.': '管理员已禁用你的视频访问权限。',
        'Contact your administrator to restore access': '请联系管理员恢复访问权限',
        'AI Active': 'AI 已启用',
        'Snapshot': '截图',
        'Fullscreen': '全屏',
        'Clear Child Selection': '清除儿童选择',
        'Click to Select Child': '点击选择儿童',
        'Press H for shortcuts': '按 H 键查看快捷键',
        'Child:': '儿童：',
        'Camera Controls': '摄像头控制',
        'Device Info': '设备信息',
        'Loading...': '加载中...',
        'Status:': '状态：',
        'Privacy Mode': '隐私模式',
        'Privacy Shield': '隐私保护',
        'Loading privacy status...': '正在加载隐私状态...',
        'Preset Positions': '预置位',
        'Go to Position': '前往位置',
        'Active Viewers': '当前观看人数',
        'No active viewers': '暂无观看用户',
        'Sleep Analysis': '睡眠分析',
        'Sleep Detection': '睡眠检测',
        'Loading presets...': '正在加载预置位...',
        'No presets available': '暂无预置位',
        'Failed to load presets': '预置位加载失败',
        'Online': '在线',
        'Offline': '离线',
        'Error': '错误',
        'Unknown': '未知',
        'Sleep': '睡眠',
        'Awake': '清醒',
        'No child': '未检测到儿童',
        'Disabled': '已禁用',
        'LIVE': '直播'
        , 'Welcome Back': '欢迎回来'
        , 'Monitor your little one securely': '安全守护您的宝宝'
        , 'Good night': '晚安'
        , 'Good morning': '早上好'
        , 'Good afternoon': '下午好'
        , 'Good evening': '晚上好'
        , 'Secure Connection': '安全连接'
        , 'SSL Encrypted': 'SSL 加密'
        , 'Username': '用户名'
        , 'Password': '密码'
        , 'Remember me': '记住我'
        , 'Sign up': '注册'
        , 'Add User': '添加用户'
        , 'Login Logs': '登录日志'
        , 'Back to Users': '返回用户列表'
        , 'User Management': '用户管理'
        , 'Manage user accounts and permissions': '管理用户账户和权限'
        , 'Active': '启用'
        , 'Inactive': '未启用'
        , 'Enabled': '已启用'
        , 'Created': '创建时间'
        , 'Last Login': '最后登录'
        , 'Actions': '操作'
    };

    function translateText(text) {
        const trimmed = text.trim();
        if (translations[trimmed]) {
            return text.replace(trimmed, translations[trimmed]);
        }
        return text
            .replace(/Privacy mode enabled/g, '隐私模式已开启')
            .replace(/Privacy mode disabled/g, '隐私模式已关闭')
            .replace(/Camera controls ready/g, '摄像头控制已就绪')
            .replace(/Failed to initialize camera controls/g, '摄像头控制初始化失败')
            .replace(/Camera moved to preset/g, '摄像头已移动到预置位')
            .replace(/Failed to set camera preset/g, '设置摄像头预置位失败');
    }

    function translatePage() {
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        const nodes = [];
        let node;
        while ((node = walker.nextNode())) {
            if (node.parentElement && !['SCRIPT', 'STYLE'].includes(node.parentElement.tagName)) {
                nodes.push(node);
            }
        }
        nodes.forEach((textNode) => {
            const translated = translateText(textNode.nodeValue || '');
            if (translated !== textNode.nodeValue) textNode.nodeValue = translated;
        });

        document.querySelectorAll('[placeholder], [title], [alt]').forEach((element) => {
            ['placeholder', 'title', 'alt'].forEach((attribute) => {
                if (element.hasAttribute(attribute)) {
                    element.setAttribute(attribute, translateText(element.getAttribute(attribute)));
                }
            });
        });
    }

    function init() {
        document.documentElement.lang = 'zh-CN';
        translatePage();
        new MutationObserver(translatePage).observe(document.body, { childList: true, subtree: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
