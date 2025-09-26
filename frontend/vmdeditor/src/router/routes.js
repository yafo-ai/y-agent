const routers = [
  {
    name: '/md',
    path: '/md',
    component: () => import(/* webpackChunkName: "md" */'@/views/md/md.vue'),
    meta: {
      title: 'markdown编辑器',
    },
  },
  {
    name: '/shoplist',
    path: '/shoplist',
    component: () => import(/* webpackChunkName: "shoplist" */'@/views/shop/list.vue'),
    meta: {
      title: '商品管理',
    },
  },
  {
    name: '/utillist',
    path: '/utillist',
    component: () => import(/* webpackChunkName: "utillist" */'@/views/util/list.vue'),
    meta: {
      title: '工具插件',
    },
  },
  {
    name: '/llmlist',
    path: '/llmlist',
    component: () => import(/* webpackChunkName: "llmlist" */'@/views/llm/list.vue'),
    meta: {
      title: '模型配置',
    },
  },
  
  {
    name: '/flowlist',
    path: '/flowlist',
    component: () => import(/* webpackChunkName: "flow" */'@/views/flow/list.vue'),
    meta: {
      title: '流程图',
    },
  },
  {
    name: '/reportflow',
    path: '/reportflow',
    component: () => import(/* webpackChunkName: "flow" */'@/views/flow/report.vue'),
    meta: {
      title: '流程日志',
    },
  },
  {
    name: '/flow',
    path: '/flow',
    component: () => import(/* webpackChunkName: "flow" */'@/views/flow/flow.vue'),
    meta: {
      title: '流程图',
      fpath: '/flowlist',
    },
  },
  
  {
    name: '/flowshare',
    path: '/flowshare',
    component: () => import(/* webpackChunkName: "flow" */'@/views/flow/flow.vue'),
    meta: {
      title: '流程图',
      fullscreen:true,
      noLogin:true,
    },
  },
  {
    name: '/login',
    path: '/login',
    component: () => import(/* webpackChunkName: "login" */'@/views/login/login.vue'),
    meta: {
      title: '登录',
      fullscreen:true,
      noLogin:true,
    },
  },
  {
    name: '/reg',
    path: '/reg',
    component: () => import(/* webpackChunkName: "login" */'@/views/login/login.vue'),
    meta: {
      title: '注册',
      noLogin:true,
      fullscreen:true,
    },
  },
  {
    name: '/userlist',
    path: '/userlist',
    component: () => import(/* webpackChunkName: "user" */'@/views/user/list.vue'),
    meta: {
      title: '用户管理',
    },
  },

  
  {
    name: 'demo/demo',
    path: '/demo',
    component: () => import(/* webpackChunkName: "demo" */'@/views/demo/demo.vue'),
    meta: {
      title: 'demo',
    },
  },
 
 
  {
    name: '/chat/detail',
    path: '/chat/detail',
    component: () => import(/* webpackChunkName: "chat" */'@/views/chat/detail.vue'),
    meta: {
      title: '知识库详情',
      noLogin:true,
    },
  },

  
  {
    name: '/app/list',
    path: '/app/list',
    component: () => import(/* webpackChunkName: "app" */'@/views/app/list.vue'),
    meta: {
      title: '管理提示词',
    },
  },
  
 
  {
    name: '/dataset/list',
    path: '/dataset/list',
    component: () => import(/* webpackChunkName: "index" */'@/views/dataset/list.vue'),
    meta: {
      title: '我的知识库',
    },
  },
  {
    name: '/test',
    path: '/test',
    component: () => import(/* webpackChunkName: "test" */'@/views/test/list.vue'),
    meta: {
      title: '流程测试',
    },
  },
  {
    name: '/unittest',
    path: '/unittest',
    component: () => import(/* webpackChunkName: "test" */'@/views/test/unittest.vue'),
    meta: {
      title: '单元测试',
    },
  },
  {
    name: '/testplan',
    path: '/testplan',
    component: () => import(/* webpackChunkName: "test" */'@/views/test/testplan.vue'),
    meta: {
      title: '测试计划',
    },
  },
  {
    name: '/testplan/detail',
    path: '/testplan/detail',
    component: () => import(/* webpackChunkName: "test" */'@/views/test/reportdetail.vue'),
    meta: {
      title: '报告详情',
      fpath:'/testplan',
    },
  },
  {
    name: '/testreport',
    path: '/testreport',
    component: () => import(/* webpackChunkName: "test" */'@/views/test/testreport.vue'),
    meta: {
      title: '测试报告',
    },
  },
  {
    name: '/testreport/detail',
    path: '/testreport/detail',
    component: () => import(/* webpackChunkName: "test" */'@/views/test/reportdetail.vue'),
    meta: {
      title: '报告详情',
      fpath:'/testreport',
    },
  },
  {
    name: '/logdetail',
    path: '/logdetail',
    component: () => import(/* webpackChunkName: "test" */'@/views/test/logdetail.vue'),
    meta: {
      title: '运行记录',
      fpath:'/test',
    },
  },
  {
    name: '/edu',
    path: '/edu',
    component: () => import(/* webpackChunkName: "test" */'@/views/edu/list.vue'),
    meta: {
      title: '语料',
    },
  },
  {
    name: '/learn',
    path: '/learn',
    component: () => import(/* webpackChunkName: "learn" */'@/views/learn/index.vue'),
    meta: {
      title: '强化学习',
    },
  },
 
  {
    name: '/dataset/excel',
    path: '/dataset/excel',
    component: () => import(/* webpackChunkName: "excel" */'@/views/excel/list.vue'),
    meta: {
      title: 'EXCEL参数库',
      fpath:'/dataset/list',
    },
  },
  {
    name: '/excel/list',
    path: '/excel/list',
    component: () => import(/* webpackChunkName: "excel" */'@/views/excel/list.vue'),
    meta: {
      title: '产品EXCEL',
      fpath:'/dataset/list',
    },
  },
  {
    name: '/excel/detail',
    path: '/excel/detail',
    component: () => import(/* webpackChunkName: "excel" */'@/views/excel/detail.vue'),
    meta: {
      title: '产品EXCEL详情',
      fpath:'/dataset/list',
    },
  },
  {
    name: '/excel/add',
    path: '/excel/add',
    component: () => import(/* webpackChunkName: "excel" */'@/views/excel/add.vue'),
    meta: {
      title: '添加产品EXCEL',
      fpath:'/dataset/list',
    },
  },

  {
    name: '/dataset/detail',
    path: '/dataset/detail',
    component: () => import(/* webpackChunkName: "index" */'@/views/dataset/detail.vue'),
    meta: {
      title: '文本知识库',
      fpath:'/dataset/list',
    },
  },
  {
    name: '/dataset/shop',
    path: '/dataset/shop',
    component: () => import(/* webpackChunkName: "shop" */'@/views/dataset/shop.vue'),
    meta: {
      title: '产品知识库',
      fpath:'/dataset/list',
    },
  },
  
]

export default routers;