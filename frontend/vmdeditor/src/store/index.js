import { createStore } from 'vuex'


const modules = {
};
// 创建一个新的 store 实例
const store = createStore({
  modules,
  state() {
    return {
      count: 0,
      token: window.localStorage.getItem('token') || '',
      username:window.localStorage.getItem('username') || '',
      defaultShopName: '好采慧自营店',
      loading: false,    //loading遮罩
      netError: false,   //网络错误
      GetWeChatConfig: null,
      Cates: [],   //分类
      iconMaps: {
        knowledgeIcons: {
          2: '<span class="iconfont icon-zhishiku" style="color:#67c23a;"></span>',
          1: '<span class="iconfont icon-zhishikuguanli" style="color:#409eff;"></span>',
          3: '<span class="iconfont icon-Excel" style="color:#196a6b;"></span>',
        },
        knowledgeNames: {
          1: { name: '文本知识库', icon: '<span class="iconfont icon-wenben_o"></span>' },
          2: { name: '产品知识库', icon: '<span class="iconfont icon-shangpin"></span>' },
          3: { name: 'EXCEL参数库', icon: '<span class="iconfont icon-Excel"></span>' },
        },
        // 流程图icon配置
        flowIcons: {
          1: '<span class="iconfont icon-flow" style="color:#67c23a;"></span>',
        },
      },
      modelTypes: {
        1: '在线GLM4模型',
        2: '本地GLM3模型',
        3: '本地Llama3模型',
        4: 'GLM3Turbo模型',
        5: 'DEEPSEEK模型',
        6: '在线GLM40520模型',
      },
      knowledgeTypes: {
        1001: '接待客服',
        2001: '知识筛选员',
        3001: '知识回答员',
        4001: 'Markdown编辑员',
        5001: '聊天记录总结员',
        6001: '测试结果测评员',
      },
      flowdata: {
        curnodeid: '',
        nodes: [],
        edges: [],
      },
      flowKeyWords: {    //流程图关键字 占用后命名不能重复
        'output': 'output',
      },

      keyTypes: {
        'String': 'String',
        'Integer': 'Integer',
        'Number': 'Number',
        'Boolean': 'Boolean',
        'Object': 'Object',
        'Array<String>': 'Array<String>',
        'Array<Integer>': 'Array<Integer>',
        'Array<Number>': 'Array<Number>',
        'Array<Boolean>': 'Array<Boolean>',
        'Array<Object>': 'Array<Object>',
      },
      keyTypesValue: {
        'String': '',
        'Integer': 0,
        'Number': 0,
        'Boolean': true,
        'Object': '{}',
        'Array<String>': '[]',
        'Array<Integer>': '[]',
        'Array<Number>': '[]',
        'Array<Boolean>': '[]',
        'Array<Object>': '[]',
      },
      socket: {},
      userData: window.localStorage.getItem('userData') || null,
      connected: false,
      soketTimer: 500,
      routeData: {},
      ComValueMap: {
        react_part_prompt: `{
"prompt_step_part":"以下是推理过程：\\n\\n{step}\\n\\n",
"prompt_think_part":"第{react_times}轮推理过程：\\n\\n{think}\\n【工具执行结果】：{return_value}\\n\\n",
"prompt_guide_part":"分析以上信息并进行思考，按照以下格式输出：\\n【思考】：填写你的分析过程\\n【工具指令】：填写你使用的工具指令，工具指令必须以\\"command=|<|\\"开始，以\\"|>|\\"结束\\n",
"prompt_end_guide_part":"请停止推理查询，使用以上信息回答问题，按照以下格式输出：\\n【思考】：填写你分析的问题答案\\n【工具指令】：填写最终回答工具指令，工具指令必须以\\"command=|<|\\"开始，以\\"|>|\\"结束\\n"
}`,
        choice_role_prompt: `assignment 工具介绍：用于从“可选角色列表”中筛选出适宜的角色，进行处理下一步任务。\nassignment 工具指令：command=|<|assignment(next_roles=[{"role":"填写选择的角色","message":"填写角色的任务内容"},{"role":"填写选择的角色","message":"填写角色的任务内容"}])|>|`,
        output_var_prompt: `write_var 工具介绍：用于将答案/结果/输出内容存储到特殊的位置。\nwrite_var 工具指令：command=|<|write_var({variables_json})|>|`
      },
      scrollbarIndex: 0,
      innerHeight: window.innerHeight,
      innerWidth: window.innerWidth,
    }
  },
  mutations: {
    SET_CONNECTION(state, connection) {
      state.socket = connection;
      state.connected = Boolean(connection);
    },
    SET_WINDOW_HEIGHT(state) {
      state.innerWidth = window.innerWidth;
      state.innerHeight = window.innerHeight;
      console.log(state.innerHeight, state.innerWidth)
    },
    Cates(state, data) {
      state.Cates = data;
    },
    flowdata(state, data) {
      state.flowdata = { ...state.flowdata, ...data };
    },
    increment(state, data) {
      state.count = data;
    },
    GetWeChatConfig(state, data) {
      state.GetWeChatConfig = data;
    },
    loading(state, data) {
      state.loading = data;
    },
    netError(state, data) {
      state.netError = data;
    },
    routeData(state, data) {
      state.routeData = data;
    },
    userData(state, data) {
      if (data) {
        window.localStorage.setItem('userData', data);
      }
      state.userData = data;
    },
    username(state, data) {
     
      if (data) {
        window.localStorage.setItem('username', data);
      } else {
        window.localStorage.removeItem('username');
        state.username = null;
      }
      state.username = data;

    },
    token(state, data) {
      console.log("token")
      if (data) {
        window.localStorage.setItem('token', data);
      } else {
        window.localStorage.removeItem('token');
        window.localStorage.removeItem('userData');
        state.userData = null;
      }
      state.token = data;

    },
    scrollbarIndex(state, data) {
      state.scrollbarIndex += 1;
    },


  },
  actions: {
    login() {
      return new Promise((resolve) => {
        resolve()
      })
    },
    updateWindowHeight({ commit }) {
      commit('SET_WINDOW_HEIGHT');
    },
    initializeWebsocket({ commit, state, dispatch }, connectionUrl) {

      state.socket[connectionUrl] = new WebSocket(connectionUrl);
      commit('SET_CONNECTION', state.socket);

      state.socket[connectionUrl].onopen = () => {
        state.soketTimer = 500;
      };

      state.socket[connectionUrl].onerror = (error) => {
        console.error('WebSocket error:', error);
        // setTimeout(() => {
        //   state.soketTimer = state.soketTimer * 2;
        //   dispatch('initializeWebsocket', connectionUrl);
        // }, state.soketTimer);
      };

      state.socket[connectionUrl].onmessage = (message) => {
        // Handle incoming messages
      };

      state.socket[connectionUrl].onclose = () => {
        state.socket[connectionUrl] = undefined;
        commit('SET_CONNECTION', state.socket);
      };
    },
    sendMessage({ state }, message) {
      if (state.connected) {
        state.socket.send(message);
      } else {
        console.error('WebSocket is not connected');
      }
    },


    setToken({ commit }, param) {
      return new Promise((resolve) => {
        commit('token', param)
        resolve()
      })
    },


  },
  getters: {
    innerWidth(state) {
      return window.innerWidth;
    },
    innerHeight(state) {
      return state.innerHeight;
    },
    scrollbarIndex(state) {
      return state.scrollbarIndex;
    },
    socket(state) {
      return state.socket;
    },
    ComValueMap(state) {
      return state.ComValueMap;
    },

    routeData(state) {
      return state.routeData;
    },

    flowKeyWords(state) {
      return state.flowKeyWords;
    },
    keyTypesValue(state) {
      return state.keyTypesValue;
    },
    flowdata(state) {
      return state.flowdata;
    },
    token(state) {
      return window.localStorage.getItem("token") || state.token;
    },
    
    username(state) {
      return window.localStorage.getItem("username") || state.username;
    },
    userData(state) {
      return window.localStorage.getItem("userData");
    },
    keyTypes(state) {
      return state.keyTypes;
    },
    modelTypes(state) {
      return state.modelTypes;
    },
    knowledgeTypes(state) {
      return state.knowledgeTypes;
    },

    iconMaps(state) {
      return state.iconMaps;
    },

  }

})


export default store;