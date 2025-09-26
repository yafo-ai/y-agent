import { cloneDeep } from 'lodash';
import axios from './axios';
// import COMMON_ENV from '@/config/env';
let BASE_URL = '/api';

if (
  import.meta.env.DEV) {
  BASE_URL = '/api';
} else {
  BASE_URL = '/api';
}

export function exportXml(xmlData, name) {
  // 创建Blob对象，注意这里xmlData应该是XML字符串形式
  const blob = new Blob([xmlData], { type: "application/xml;charset=utf-8" });
  // 创建下载链接
  const url = URL.createObjectURL(blob);
  // 创建a标签并模拟点击以触发下载
  const a = document.createElement('a');
  a.href = url;
  let curname = name || Date.now() + '.xml';
  a.download = curname; // 设置下载文件的名称
  document.body.appendChild(a);
  a.click();
  // 清理并移除元素
  document.body.removeChild(a);
  // 释放URL对象
  URL.revokeObjectURL(url);
}

export function exportJson(jsonData, name) {
  // 将JSON对象转换为字符串
  const jsonString = JSON.stringify(jsonData, null, 2); // 使用缩进
  // 创建Blob对象
  const blob = new Blob([jsonString], { type: "application/json;charset=utf-8" });
  // 创建下载链接
  const url = URL.createObjectURL(blob);
  // 创建a标签并模拟点击以触发下载
  const a = document.createElement('a');
  a.href = url;
  let curname = name || Date.now() + '.json';
  a.download = curname; // 设置下载文件的名称
  document.body.appendChild(a);
  a.click();
  // 清理并移除元素
  document.body.removeChild(a);
  // 释放URL对象
  URL.revokeObjectURL(url);
}

export function importJson(file) {
  return new Promise((resolve, reject) => {
    if (!file) {
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const content = e.target.result;
        try {
            const jsonData = JSON.parse(content);
            // let res = JSON.stringify(jsonData, null, 2); // 格式化显示JSON内容
            resolve(jsonData);
        } catch (error) {
          reject(error)
        }
    };
    reader.readAsText(file);
  })
}


export function download(src, callback) {

  axios.get(src, { isfile: true, responseType: 'blob', }).then((res) => {
    let blob = res.data;
    let cdis = "";
    if (res.headers['content-disposition'].indexOf('filename=') !== -1) {
      cdis = res.headers['content-disposition'].split('filename=')[1].replace(/"/g, '');
    } else if (res.headers['content-disposition'].indexOf("filename*=utf-8''") !== -1) {
      cdis = res.headers['content-disposition'].split("filename*=utf-8''")[1].replace(/"/g, '')
    }
    console.log(cdis, decodeURIComponent(cdis))
    const filename = decodeURIComponent(cdis);

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename; // 可手动指定或从响应头获取文件名
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(url); // 释放内存
    document.body.removeChild(link);
    if (typeof callback === 'function') {
      callback(true);
    }
  })
    .catch(error => {
      if (typeof callback === 'function') {
        callback(true);
      }
      window._this.$message('下载失败,文件不存在或已失效', 'error');
    });

};



export function upload(params) {
  let url = '/files/upload/images';
  let config = {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  };
  let param = new FormData();
  param.append('file', params.file);
  return axios.post(BASE_URL + url, param, config);
}

export function train_case_export(params) {
  //导出
  download(BASE_URL + '/train/train_case_export?cate_id=' + params.cate_id, function (flag) {
    if (!flag) {
      window._this.$message('导出失败');
    }
  });
}


export function unit_case_export(params) {
  //导出
  download(BASE_URL + '/test/case/unit/export?cate_id=' + params.cate_id, function (flag) {
    if (!flag) {
      window._this.$message('导出失败');
    }
  });
}
export function get_cates(params) {
  let url = '/train/get_cates';

  return axios.get(BASE_URL + url, {
    params
  });
}
export function testcaseresult(params) {
  let url = '/test/case/result/' + params.id;

  return axios.get(BASE_URL + url, {});
}
export function model_configall(params, TEST_TYPE) {
  if (TEST_TYPE) {
    params ? params.tag = TEST_TYPE : params = { tag: TEST_TYPE };
  }
  let url = '/model_config/all';
  return axios.get(BASE_URL + url, {
    params
  });
}
export function model_configallget(params) {
  let url = '/model_config/get/' + params.id;
  return axios.get(BASE_URL + url, {});
}

export function tools(params) {
  let url = '/tools';
  return axios.get(BASE_URL + url, {
    params
  });
}

export function gettools(params) {
  let url = '/tools/get/' + params.id;
  return axios.get(BASE_URL + url, {});
}

export function platformlist(params) {
  // 获取平台列表
  let url = '/goods/platform/list';
  return axios.get(BASE_URL + url, params);
}

export function user(params) {
  // 用户详情
  let url = '/user/' + params.id;
  return axios.get(BASE_URL + url, {});
}

export function useradd_role(params) {
  // 用户增加角色/api/user/{id}/add_role
  let url = '/user/' + params.id + '/add_role';
  return axios.get(BASE_URL + url, params);
}

export function role(params) {
  // 角色详情
  let url = '/user/role/' + params.id;
  return axios.get(BASE_URL + url, params);
}

export function menurefresh(params) {
  // 刷新菜单
  let url = '/menu/refresh';
  return axios.get(BASE_URL + url, params);
}

export function promptstree(params) {
  // 刷新菜单
  let url = '/prompts/prompts/type/tree';
  return axios.get(BASE_URL + url, params);
}

export function workflowall(params) {
  // 刷新菜单
  let url = '/workflow/list/all';
  return axios.get(BASE_URL + url, {});
}

export function promptstreeadd(params) {
  // 获取菜单
  let url = '/prompts/prompts/type/add';
  if (params.id) {
    url = '/prompts/prompts/type/edit';
  }
  return axios.post(BASE_URL + url, params);
}

export function filesname(params) {
  // 获取文件
  let url = '/files/'+params.name;
  return axios.post(BASE_URL + url, {});
}


export function filesuploads(params,type) {
  // 单文件上传  
  let url = '/files/upload_single';
  if(type){
    // 多文件上传
    url = '/files/uploads';
  }
  return axios.post(BASE_URL + url, params);
}


export function try_answer(params) {
  // 获取菜单
  let url = '/test/case/unit/generate_answer';
  return axios.post(BASE_URL + url, params, { isHideLoading: true });
}
export function node_run_debug(params,type) {
  // 节点调试
  let url = '/workflow/node_run_debug';
  if(type == '1'){
    // 调试提示词
    url = '/workflow/node_prompt_debug'
  }
  return axios.post(BASE_URL + url, params);
}

export function node_prompt_debug(params) {
  // 节点调试
  let url = '/workflow/node_prompt_debug';
 
  return axios.post(BASE_URL + url, params);
}

export function menu(params) {
  // 获取菜单
  let url = '/menu';
  return axios.post(BASE_URL + url, params);
}

export function updatesxl(params,type) {
  // 更新向量库
  let url = '/documents/batch_convert_index/'+params.knowledgebase_id;
  if(type){
    // 产品知识库
    url = '/filedatabase/batch_convert_index/'+params.knowledgebase_id;
  }
  return axios.post(BASE_URL + url, {});
}

export function menutree(params) {
  // 获取菜单树
  let url = '/menu/tree';
  return axios.post(BASE_URL + url, params);
}

export function menuadd(params) {
  // 新增菜单
  let url = '/menu/add';
  if (params.id) {
    url = '/menu/' + params.id + '/update';
  }
  return axios.post(BASE_URL + url, params);
}

export function menudelete(params) {
  // 菜单删除
  let url = '/menu/' + params.id + '/delete';
  return axios.post(BASE_URL + url, params);
}

export function roleadd(params) {
  // 角色新增
  let url = '/user/role/add';
  if (params.id) {
    url = '/user/role/' + params.id + '/update';
  }
  return axios.post(BASE_URL + url, params);
}

export function rolepaged(params) {
  // 角色查询
  let url = '/user/role/paged';
  return axios.post(BASE_URL + url, params);
}
export function roledelete(params) {
  // 角色删除
  let url = '/user/role/' + params.id + '/delete';
  return axios.post(BASE_URL + url, params);
}

export function roleauthorize_menu(params) {
  // 角色授权菜单
  let url = '/user/role/authorize_menu';
  return axios.post(BASE_URL + url, params);
}

export function userauthorize_menu(params) {
  // 用户授权菜单
  let url = '/user/' + params.id + '/authorize_menu';
  return axios.post(BASE_URL + url, params);
}
export function useractivate(params) {
  // 用户激活
  let url = '/user/' + params.id + '/activate';
  return axios.post(BASE_URL + url, params);
}
export function userreset_password(params) {
  // 重置密码
  let url = '/user/' + params.id + '/reset_password';
  return axios.post(BASE_URL + url, params);
}
export function userdelete(params) {
  // 用户删除
  let url = '/user/' + params.id + '/delete';
  return axios.post(BASE_URL + url, params);
}
export function userpaged(params) {
  // 用户查询
  let url = '/user/paged';
  return axios.post(BASE_URL + url, params);
}
export function useradd(params) {
  // 用户新增修改
  let url = '/user/add';
  if (params.id) {
    url = '/user/' + params.id + '/update';
  }
  return axios.post(BASE_URL + url, params);
}

export function shopadd(params) {
  // 编辑/新增---店铺信息 id": 0, "platform_id": 0, "shop_name": "string"
  let url = '/goods/shop/add';
  // if(params.id) {
  //   url = '/tools/edit/'+params.id;
  // }
  return axios.post(BASE_URL + url, params);
}

export function login(params) {
  // 登录
  let url = '/authorize/login';
  return axios.post(BASE_URL + url, params, {
    isCancel: true,
    isNoToken: true,
  });
}
export function register(params) {
  // 登录
  let url = '/authorize/register';
  return axios.post(BASE_URL + url, params, {
    isCancel: true,
    isNoToken: true,
  });
}
export function shoplist(params) {
  // platform_id 获取店铺列表
  let url = '/goods/shop/list';
  return axios.post(BASE_URL + url, params);
}

export function shopdelete(params) {
  // 删除店铺信息
  let url = '/goods/shop/delete/' + params.id;
  return axios.post(BASE_URL + url, {});
}

export function categorieslist(params) {
  // 获取店铺分类列表
  let url = '/goods/categories/list';
  return axios.post(BASE_URL + url, params);
}

export function categoriesadd(params) {
  // 编辑/新增---店铺分类信息  "id": 0, "name": "string", "parent_id": 0
  let url = '/goods/category/add';
  // if(params.id) {
  //   url = '/tools/edit/'+params.id;
  // }
  return axios.post(BASE_URL + url, params);
}

export function categoriesdelete(params) {
  // 删除分类信息
  let url = '/goods/category/delete/' + params.id;
  return axios.post(BASE_URL + url, {});
}

export function profileadd(params) {
  // 编辑/新增---商品档案信息
  // "id": 0,
  // "goods_name": "string",
  // "goods_code": "string",
  // "barcode": "string",
  // "category_id": 0
  let url = '/goods/profile/add';
  // if(params.id) {
  //   url = '/tools/edit/'+params.id;
  // }
  return axios.post(BASE_URL + url, params);
}


export function profilepaged(params) {
  // 获取商品档案列表
  // "page_index": 1,
  // "page_size": 10,
  // "name": "string",
  // "goods_code": "string",
  // "barcode": "string",
  // "category_id": 0
  let url = '/goods/profile/paged';
  return axios.post(BASE_URL + url, params);
}

export function profiledelete(params) {
  // 删除商品档案列表
  let url = '/goods/profile/delete/' + params.id;
  return axios.post(BASE_URL + url, {});
}

export function goodsadd(params) {
  // 编辑/新增---商品信息
  // :param id: 商品ID
  // :param shop_id: 所属店铺
  // :param category_id: 所属类目
  // :param sku: 商品sku
  // :param suite_flag: 是否套装商品
  // :param recommend_flag: 是否推荐商品
  // :param price: 零售价
  // :param on_sale_flag: 上下架标记
  // :param sale_point: 商品卖点
  // :param profile_tuple: 关联的商品档案列表[(商品档案id, 配置数量, 商品mapping表id)]
  let url = '/goods/add';
  // if(params.id) {
  //   url = '/tools/edit/'+params.id;
  // }
  return axios.post(BASE_URL + url, params);
}

export function goodsdetail(params) {
  // 获取商品详情
  let url = '/goods/detail/' + params.id;
  return axios.get(BASE_URL + url, {});
}

export function goodsdelete(params) {
  // 删除商品
  let url = '/goods/delete/' + params.id;
  return axios.post(BASE_URL + url, {});
}

export function goodspaged(params) {
  // 获取商品列表
  // "page_index": 1,
  // "page_size": 10,
  // "category_id": 0,
  // "sku": "string",
  // "shop_id": 0
  let url = '/goods/paged';
  return axios.post(BASE_URL + url, params);
}





export function toolsadd(params) {
  let url = '/tools/add';
  if (params.id) {
    url = '/tools/edit/' + params.id;
  }

  return axios.post(BASE_URL + url, params);
}

export function toolsdelete(params) {
  let url = '/tools/delete/' + params.id;
  return axios.post(BASE_URL + url, {});
}

export function set_disabled(params) {
  let url = '/tools/set_disabled/' + params.id;
  return axios.post(BASE_URL + url, {});
}

export function model_configdelete(params) {
  let url = '/model_config/delete/' + params.id;
  return axios.post(BASE_URL + url, params);
}

export function model_configadd(params) {
  let url = '/model_config/add';
  if (params.id) {
    url = '/model_config/edit/' + params.id;
  }
  return axios.post(BASE_URL + url, params);
}



export function testcate(params, TEST_TYPE) {
  if (TEST_TYPE) {
    params ? params.tag = TEST_TYPE : params = { tag: TEST_TYPE };
  }
  let url = '/test/cate';
  return axios.get(BASE_URL + url, {
    params
  });
}
export function testcateadd(params, TEST_TYPE) {
  if (TEST_TYPE) {
    params ? params.tag = TEST_TYPE : params = { tag: TEST_TYPE };
  }
  let url = '/test/cate/add';
  if (params.id) {
    url = '/test/cate/edit/' + params.id;
  }
  return axios.post(BASE_URL + url, params);
}
export function add_update(curparams,type) {
  let params = cloneDeep(curparams)
  let url = '/workflow/view_edit';
  if(type == 'baseinfo'){
    if(params.id){
      url = '/workflow/baseinfo/update'
    }else{
      url = '/workflow/baseinfo/add'
    }
    delete params.view_json
  }else{
    params = {
      id:params.id,
      view_json:params.view_json
    }
  }
  
  return axios.post(BASE_URL + url, params);
}
export function workflowdelete(params) {
  let url = '/workflow/' + params.id + '/delete';
  return axios.post(BASE_URL + url, params);
}

export function get_log_scores(params) {
  let url = '/workflow/log/scores';
  return axios.get(BASE_URL + url, {
    params
  });
}

export function workflowcopy(params) {
  let url = '/workflow/copy?flow_id='+params.flow_id;
  return axios.post(BASE_URL + url, {});
}

export function get_log_detail(params) {
  let url = '/workflow/log/detail/' + params.id;
  return axios.get(BASE_URL + url, {});
}


export function workflowrun(params,routepath) {
  let url = '/workflow/run';
  // if(routepath== "/flowshare"){
  //   // 分享页面
  //   url = '/workflow/share_run';
  // }

  // delete params.id;
  return axios.post(BASE_URL + url, params);
}

export function tool_flows() {
  let url = '/workflow/tool_flows';
  // delete params.id;
  return axios.post(BASE_URL + url, {});
}

export function workflowinput(params) {
  let url = '/workflow/' + params.id + '/input';
  return axios.get(BASE_URL + url, {});
}
export function workflowget(params, routepath) {
  let url = '/workflow/' + params.id;
  if(routepath== "/flowshare"){
    // 分享页面  用其他接口
    url = '/workflow/shareinfo/' + params.id;
    params = {api_key:params.api_key}
  }else{
    // params = {api_key:params.api_key}
    params = undefined
  }
  return axios.get(BASE_URL + url, {params});
}

export function config() {
  let url = '/config';
  return axios.get(BASE_URL + url, {});
}

export function batch_update(params) {

  let url = '/config/batch_update';
  return axios.post(BASE_URL + url, {configs:params});
}

export function workflow(params, TEST_TYPE) {
  if (TEST_TYPE) {
    params ? params.tag = TEST_TYPE : params = { tag: TEST_TYPE };
  }
  let url = '/workflow';
  return axios.post(BASE_URL + url, params);
}
export function workflowlogs_pagination(params, TEST_TYPE) {
  if (TEST_TYPE) {
    params ? params.tag = TEST_TYPE : params = { tag: TEST_TYPE };
  }
  let url = '/workflow/logs_pagination';
  return axios.post(BASE_URL + url, params);
}


export function move_cate(params, TEST_TYPE) {
  if (TEST_TYPE) {
    params ? params.tag = TEST_TYPE : params = { tag: TEST_TYPE };
  }
  let url = '/test/case/move_cate';
  return axios.post(BASE_URL + url, params);
}
export function trainunit_cases(params) {

  let url = '/train/unit_cases';
  return axios.post(BASE_URL + url, params);
}

export function unittrain_cases(params) {

  let url = '/test/case/unit/train_cases';
  return axios.post(BASE_URL + url, params);
}
export function trainmove_cate(params) {

  let url = '/train/move_cate';
  return axios.post(BASE_URL + url, params);
}
export function testcaseadd(params, TEST_TYPE) {
  if (TEST_TYPE) {
    params ? params.tag = TEST_TYPE : params = { tag: TEST_TYPE };
  }
  let url = '/test/case/add';

  if (params.id) {
    url = '/test/case/edit/' + params.id;
    if (TEST_TYPE == "S") {
      // 添加单元测试

      url = '/test/case/unit/edit/' + params.id;
      params = {
        cate_id: params.cate_id,
        question: params.question,
        right_answer: params.right_answer,
        note: params.note,
        test_standard: params.test_standard || "",
        is_marked: params.is_marked,
        is_modified: params.is_modified,
      }
    }
  } else {
    if (TEST_TYPE == "S") {


      // 添加单元测试手动添加
      url = '/test/case/unit/add/new';
      params = {
        cate_id: params.cate_id,
        question: params.question,
        right_answer: params.right_answer,
        note: params.note,
        test_standard: params.test_standard || "",
        workflow_node_log_id: params.workflow_node_log_id || undefined,
        is_marked: params.is_marked,
        is_modified: params.is_modified,
      }


    }
  }
  return axios.post(BASE_URL + url, params);
}
export function testcasedelete(params, TEST_TYPE) {
  if (TEST_TYPE) {
    params ? params.tag = TEST_TYPE : params = { tag: TEST_TYPE };
  }
  let url = '/test/case/delete/' + params.id;
  return axios.post(BASE_URL + url, {});
}
export function testcatedelete(params, TEST_TYPE) {
  if (TEST_TYPE) {
    params ? params.tag = TEST_TYPE : params = { tag: TEST_TYPE };
  }
  let url = '/test/cate/delete/' + params.id;
  return axios.post(BASE_URL + url, {});
}
export function testcasepagination(params, TEST_TYPE) {
  if (TEST_TYPE) {
    params ? params.tag = TEST_TYPE : params = { tag: TEST_TYPE };
  }
  let url = '/test/case/pagination';
  return axios.post(BASE_URL + url, params);
}

export function testplanreport(params) {
  let url = '/testplan/report';
  return axios.post(BASE_URL + url, params);
}

export function testplanreportpagination(params) {
  let url = '/testplan/report/' + params.id + '/pagination';
  return axios.post(BASE_URL + url, params);
}

export function testplanreportdelete(params) {
  let url = '/testplan/report/' + params.id + '/delete';
  return axios.post(BASE_URL + url, {});
}

export function testplanreportId(params) {
  let url = '/testplan/report/' + params.id;
  return axios.get(BASE_URL + url, {});
}
export function testplanreports(params) {
  let url = '/testplan/' + params.id + '/reports';
  return axios.get(BASE_URL + url, {});
}
export function testplanrelation_cate_case(params) {
  let url = '/testplan/' + params.id + '/relation_cate_case';
  return axios.get(BASE_URL + url, {});
}


export function testplanpagination(params) {
  let url = '/testplan/pagination';
  return axios.post(BASE_URL + url, params);
}

export function testplanadd(params) {
  let url = '/testplan/add';

  if (params.id) {
    url = '/testplan/edit';
    if (params.tag == "S") {
      url = '/testplan/unit/edit'
    }
  } else {
    if (params.tag == "S") {
      url = '/testplan/unit/add'
    }
  }
  return axios.post(BASE_URL + url, params);
}

export function testplandelete(params) {
  let url = '/testplan/delete/' + params.id;
  return axios.post(BASE_URL + url, {});
}
export function testplanrelation_cate(params) {
  let url = '/testplan/relation_cate/' + params.id;
  return axios.post(BASE_URL + url, params.cates);
}

export function testplanrelation_case(params) {
  let url = '/testplan/relation_case/' + params.id;
  return axios.post(BASE_URL + url, params.cates);
}
export function testplanbatch_execute(params,is_continue) {
  let url = '/testplan/batch_execute';
  if(is_continue){
    // 继续执行接口
    url = '/testplan/batch_execute/continue'
  }
  return axios.post(BASE_URL + url, params);
}



export function testcasebatch_execute(params, TEST_TYPE) {
  if (TEST_TYPE) {
    params ? params.tag = TEST_TYPE : params = { tag: TEST_TYPE };
  }
  let url = '/test/case/batch_execute';
  if (TEST_TYPE == "S") {
    // 执行单元测试用例
    url = '/test/case/unit/batch_execute';
  }
  return axios.post(BASE_URL + url, params);
}

export function cate_add(params) {
  let url = '/train/cate_add';
  if (params.id) {
    url = '/train/cate_edit/' + params.id;
  }
  return axios.post(BASE_URL + url, params);
}
export function cate_delete(params) {
  let url = '/train/cate_delete/' + params.id;
  return axios.post(BASE_URL + url, {});
}
export function train_case_delete(params) {
  let url = '/train/train_case_delete/' + params.id;
  return axios.post(BASE_URL + url, {});
}
export function train_case_add(params) {
  let url = '/train/train_case_add';
  if (params.id) {
    url = '/train/train_case_update';
  }
  return axios.post(BASE_URL + url, params);
}

export function get_train_cases(params) {
  let url = '/train/get_train_cases';
  return axios.post(BASE_URL + url, params);
}



export function database(params) {
  let url = '/filedatabase';
  return axios.get(BASE_URL + url, {
    params
  });
}

export function databaseDelete(params) {
  let url = '/filedatabase/delete/' + params.id;
  return axios.post(BASE_URL + url, {});
}



export function databaseDetail(params) {
  let url = '/filedatabase/detail/' + params.id + '?code=' + params.code;
  return axios.get(BASE_URL + url, {});
}
export function databaseDetailContents(params) {
  let url = '/filedatabase/detail/' + params.id + '/contents';
  return axios.post(BASE_URL + url, params);
}

export function databaseIndex(params) {
  let url = '/filedatabase/converter_index/' + params.id;
  return axios.post(BASE_URL + url, {});
}

export function similaritysearch(params) {
  let url = '/chats/similarity_search';
  return axios.post(BASE_URL + url, params);
}
export function promptstreedelete(params) {
  let url = '/prompts/prompts/type/' + params.id + '/delete';
  return axios.post(BASE_URL + url, {});
}

export function prompts(data) {
  let url = '/prompts?page=1&pagesize=10000';
  let params = { ...data }
  if (data.type) {

    url = '/prompts/list/by_prompt_type';
    // params = {}
  } else {
    url = '/prompts';
  }
  return axios.get(BASE_URL + url, { params });
}

export function promptsversions(id) {
  let url = '/prompts/' + id + '/versions';

  return axios.get(BASE_URL + url, {});
}




export function mcp_provider(params) {
  let url = '/mcp_provider';
  return axios.get(BASE_URL + url, {params});
}

export function mcp_providerid(params) {
  let url = '/mcp_provider/'+params.id;

  return axios.get(BASE_URL + url, {});
}

export function mcp_providercreate(params) {
  let url = '/mcp_provider/create';
  if(params.id) {
    url = '/mcp_provider/update';
  }
  return axios.post(BASE_URL + url, params);
}

export function mcp_providerdelete(params) {
  let url = '/mcp_provider/delete/' + params.id;
  return axios.post(BASE_URL + url, {});
}
export function mcp_providerreconnect(params) {
  let url = '/mcp_provider/reconnect/' + params.id;
  return axios.post(BASE_URL + url, {});
}

export function select_tools(params) {
  let url = '/mcp_provider/select_tools';
  return axios.post(BASE_URL + url, params);
}


export function categorytree() {
  let url = '/workflow/category/tree';

  return axios.get(BASE_URL + url, {});
}
export function mcp_providerlist() {
  let url = '/mcp_provider/tools/list ';

  return axios.get(BASE_URL + url, {});
}



export function categoryadd(params) {
  let url = '/workflow/category/add';
  if(params.id) {
    url = '/workflow/category/edit';
  }

  return axios.post(BASE_URL + url, params);
}

export function categorydelete(params) {
  let url = '/workflow/category/' + params.id+'/delete';
  return axios.post(BASE_URL + url, {});
}

export function promptsversionsDetail(data) {
  let url = '/prompts/' + data.id + '/version/detail/' + data.ver;
  return axios.get(BASE_URL + url, {});
}
export function productsmove(params) {
  let url = '/products/move/' + params.id + '?target_pid=' + params.target_pid;
  return axios.post(BASE_URL + url, {});
}

export function promptsGet(params) {
  const url = '/prompts/' + params.id;
  return axios.get(BASE_URL + url, {});
}

export function promptsDelete(params) {
  const url = '/prompts/delete/' + params.id;
  return axios.post(BASE_URL + url, {});
}

export function promptsAdd(data) {
  let url = '/prompts/add';
  if (data.id) {
    url = '/prompts/edit/' + data.id;
  }
  return axios.post(BASE_URL + url, data, {
    isCancel: true
  });
}

export function products(params) {

  const url = '/products';
  return axios.get(BASE_URL + url, {
    params
  });
}
export function productsGet(params) {
  const url = '/products/get/' + params.id;
  return axios.get(BASE_URL + url, {});
}

export function productsGettemp(params) {

  const url = '/products/get_template';
  return axios.get(BASE_URL + url, {
    params
  });
}

export function productsAdd(data) {
  let url = '/products/add';
  if (data.id) {
    url = '/products/edit/' + data.id;
  }
  return axios.post(BASE_URL + url, data, {
    isCancel: true
  });
}

export function productsEdit(data) {
  let url = '/products/edit/' + data.id;
  return axios.post(BASE_URL + url, data);
}

export function productsDelete(data) {
  let url = '/products/delete/' + data.id;
  return axios.post(BASE_URL + url, data);
}

export function productsIndex(data) {
  let url = '/products/converter_index/' + data.id;
  return axios.post(BASE_URL + url, data);
}


export function documents(params) {
  const url = '/documents/';
  return axios.get(BASE_URL + url, {
    params
  });
}
export function documentsGet(params) {
  const url = '/documents/get/' + params.id;
  return axios.get(BASE_URL + url, {
    params
  });
}



export function documentsEdit(data, isIndex) {
  let url = '/documents/edit/' + data.id + '/content';
  let params = {
    name: data.name
  }
  if (data.is_markdown) {
    url = '/documents/edit/' + data.id + '/markdown_content';
    if (isIndex) {
      url = '/documents/edit/' + data.id + '/markdown_content_to_index';
    }
    params.markdown_content = data.text;
  } else {
    params.content = data.text;
  }
  return axios.post(BASE_URL + url, params, {
    isCancel: true,
    headers: {
      'Content-Type': 'application/json'
    }
  });
}

export function documentsHistoryDetail(params) {
  const url = '/documents/' + params.id + '/version/detail/' + params.ver;
  return axios.get(BASE_URL + url, {});
}


export function documentsHistory(data) {
  let url = '/documents/' + data.id + '/versions';

  return axios.get(BASE_URL + url, {});
}




export function simpleChat(data) {
  let url = '/chats/simple_chat';

  return axios.post(BASE_URL + url, data, {
    headers: {
      'Content-Type': 'application/json'
    }
  });
}

export function chat(data) {
  let url = '/chats/agent_chat';
  return axios.post(BASE_URL + url, data, {
    headers: {
      'Content-Type': 'application/json'
    }
  });
}


export function documentsAddMarkDown(data) {
  let url = '/documents/add_content';

  return axios.post(BASE_URL + url, data);
}

export function documentsEditMd(data) {
  let url = '/documents/edit/' + data.id + '/markdown_content';

  return axios.post(BASE_URL + url, data.text + '', {
    isCancel: true
  });
}


export function documentsMove(data) {
  let url = '/documents/move?category_id=' + data.category_id + '&target_category_id=' + data.target_category_id;
  if (data.id) {
    url = '/documents/move/' + data.id + '?target_category_id=' + data.target_category_id;
  }
  return axios.post(BASE_URL + url, {});
}

export function documentsConverter(data) {
  let url = '/documents/converter_index/' + data.id;
  return axios.post(BASE_URL + url, data);
}

export function documentsMarkdown(data) {
  let url = '/documents/converter_markdown/' + data.id;
  return axios.post(BASE_URL + url, data);
}


export function documentsDelete(data) {
  let url = '/documents/delete/' + data.id;
  return axios.post(BASE_URL + url, {});
}

export function documentsDeleteIndex(data) {
  let url = '/documents/delete/' + data.id + '/index';
  return axios.post(BASE_URL + url, {});
}

export function categories(params) {
  const url = '/categories/';
  return axios.get(BASE_URL + url, {
    params
  });
}

export function categoriesDelete(data) {
  let url = '/categories/delete/' + data.id;
  return axios.post(BASE_URL + url, {});
}

export function categoriesAdd(data) {
  let url = '/categories/add';
  if (data.id) {
    url = '/categories/edit/' + data.id;
  }
  return axios.post(BASE_URL + url, data, {
    isCancel: true
  });
}
export function knowledges(params) {
  const url = '/knowledgebases/';
  return axios.get(BASE_URL + url, {
    params,
    isHideLoading: false
  });
}

export function knowledgesGet(params) {
  const url = '/knowledgebases/get/' + params.id;
  return axios.get(BASE_URL + url, {});
}







export function knowledgesAdd(data) {
  let url = '/knowledgebases/add';
  if (data.id) {
    url = '/knowledgebases/edit/' + data.id;
  }
  return axios.post(BASE_URL + url, data, {
    isCancel: true
  });
}

export function knowledgesDelete(data) {
  let url = '/knowledgebases/delete/' + data.id;
  return axios.post(BASE_URL + url, {});
}