<script setup>
import { ref, onMounted, onBeforeUnmount, reactive, watch } from "vue";
import { useStore } from "vuex";
import { useRoute, useRouter } from "vue-router";

import * as monaco from "monaco-editor";

import { cloneDeep } from "lodash"; // 引入lodash库的cloneDeep方法进行深拷贝
const props = defineProps({
  nodes: {
    type: [Array],
    default: () => [],
  },
  edges: {
    type: [Array],
    default: () => [],
  },
  nodeid: {
    type: String,
    default: "",
  },
  lineNumbers: {
    type: String,
    default: "off",
  },
  fontSize: {
    type: [String, Number],
    default: 12,
  },

  language: {
    type: String,
    default: "python",
  },
  modelValue: { type: String, default: "" },
});
const emits = defineEmits(["subfn", "update:modelValue"]);
const route = useRoute();
const router = useRouter();
const store = useStore();

const dialogFormVisible = ref(false);

const editorContainer = ref(null);
let editorInstance = null;

const COM_POS0 = '$0';  //鼠标位置
const COM_POS1 = '$1';  //tab 第二次位置  ${1:"Hello"}替换文本

const COM_DICT = [
  {
    sym: ' ',  //触发字符 空格
    children: [
      {
        label: '强调输出格式的指令',
        detail: '当大模型输出指令经常错的时候,添加此提示词',
        insertText: '注意:工具指令不可篡改,不可遗漏,必须以command=|<|开始，以|>|结束。' + COM_POS0,
      },
      {
        label: 'send_message',
        detail: '向聊天室发送消息',
        insertText: 'command=|<|send_message(receiver="填写接受消息的角色名称",message="填写消息的内容") |>|' + COM_POS0,
      }, {
        label: 'notify',
        detail: '向用户发送消息（发送完流程继续运行）',
        insertText: 'command=|<|notify(message="填写消息的内容")|>|' + COM_POS0,
      }, {
        label: 'terminate',
        detail: '向用户发送消息（发送完流程终止）',
        insertText: 'command=|<|terminate(message="向用户发消息此处可以填写固定值或者变量")|>|' + COM_POS0,
      }, {
        label: 'write_var',
        detail: '写入space工作空间环境变量',
        insertText: 'command=|<|write_var(参数名=值,参数名=值)|>|' + COM_POS0,
      }, {
        label: 'assignment',
        detail: '指定选择某个下游节点角色执行后续流程',
        insertText: 'command=|<|assignment(next_roles=[{"role":"角色1","message":"消息1"},{"role":"角色2","message":"消息2"}])|>|' + COM_POS0,
      }, {
        label: 'if',
        detail: 'if代码块',
        insertText: '{% if  ' + COM_POS0 + ' %}\r\n\r\n{% else %}\r\n\r\n{% endif %}',
      }, {
        label: 'for',
        detail: 'for代码块',
        insertText: '{% for v in ${1:变量名称} %}\r\n{{v}}\r\n{% endfor %}',
      }, {
        label: 'batch',
        detail: 'batch代码块，批处理使用的内部临时变量，batch存储的是，当前批次的数据集',
        insertText: '{{batch' + COM_POS0 + '}}',
      }, {
        label: 'for_batch例子',
        detail: '案例::for循环遍历，当前批次存储的数据集',
        insertText: '{% for doc in batch.item %}\r\ndoc.id\r\n{% endfor %}',
      },
    ]
  },
  {
    sym: 'batch',
    isIndex: true,  // 索引触发，而非前缀匹配触发
    children: [
      {
        sym: 'index',
        label: 'index',
        detail: '当前批次的序号',
        insertText: 'index',
      }, {
        sym: 'item',
        label: 'item',
        detail: '当前批次存储的数据集，可以用for循环遍历',
        insertText: 'item',
      }, {
        sym: 'item[n]',
        label: 'item[n]',
        detail: '指定取本批次的第n条数据，n为从0开始的整数',
        insertText: 'item[${1:0}]',
      },
    ]
  },
  {
    sym: 'sys',
    isIndex: true,  // 索引触发，而非前缀匹配触发
    children: [
    {
        sym: 'space',
        label: 'space',
        detail: '工作空间',
        insertText: 'space' + COM_POS0,
        children: [
          {
            sym: '',
            label: '',
            detail: '获取当前流程工作空间变量加入提示',
            type: 'space',
          }
        ]
      },{
        sym: 'chat_room',
        label: 'chat_room',
        detail: '聊天室，不可以直接使用，必须使用其中的方法或者属性',
        insertText: 'chat_room' + COM_POS0,
        children: [
          {
            sym: 'get_talks()',
            endlen: 1,
            label: 'get_talks()',
            detail: '返回聊天详细信息 id、message、time、sender、receiver',
            insertText: 'get_talks()' + COM_POS0,
            children: [
              {
                sym: 'first(',
                label: 'first(n)',
                detail: '最早的n条',
                insertText: 'first(n)' + COM_POS0,
              }, {
                sym: 'last(',
                label: 'last(n)',
                detail: '最后n条',
                insertText: 'last(n)' + COM_POS0,
              }, {
                sym: 'message',
                label: 'message',
                detail: '返回所有符合条件的聊天内容',
                insertText: 'message' + COM_POS0,
                children: [
                  {
                    label: 'first(n)',
                    detail: '最早的n条',
                    insertText: 'first(n)' + COM_POS0,
                  }, {
                    label: 'last(n)',
                    detail: '最后n条',
                    insertText: 'last(n)' + COM_POS0,
                  }
                ]

              },
            ]
          }, {
            sym: 'get_talks("',
            endlen: 4,
            isIndex: true,

            label: '.get_talks("发送者","接收者")',
            detail: 'get_talks的另外写法',
            insertText: 'get_talks("发送者","接收者")' + COM_POS0,
            children: [
              {
                sym: 'message',
                label: 'message',
                detail: '返回聊天详细信息 id、message、time、sender、receiver',
                insertText: 'message' + COM_POS0,
                children: [
                  {
                    label: 'first(n)',
                    detail: '时间最早的n条',
                    insertText: 'first(n)' + COM_POS0,
                  }, {
                    label: 'last(n)',
                    detail: '最后n条',
                    insertText: 'last(n)' + COM_POS0,
                  }
                ]

              },
            ]
          }
        ]
      },{
        label: 'is_null_or_empty()',
        detail: '判断变量是否null或者为空（包括数组长度为0的情况）',
        insertText: 'is_null_or_empty(${1:变量名})' + COM_POS0,
      }, {
        label: 'contains(A,B)',
        detail: '查询字符串A是否包含字符串B',
        insertText: 'contains("字符串1","字符串2")' + COM_POS0,
      },{
        label: 'time()',
        detail: '当前服务器时间 HH:MM:SS',
        insertText: 'time()' + COM_POS0,
      }, {
        label: 'date()',
        detail: '当前服务器日期 YYYY-MM-DD',
        insertText: 'date()' + COM_POS0,
      }, {
        label: 'datetime()',
        detail: '当前服务器日期时间',
        insertText: 'datetime()' + COM_POS0,
      },  {
        label: 'get_documents_text()',
        detail: '根据文档id获取文档内容',
        insertText: 'get_documents_text()([${1:id1},${2:id2}])])',
      }, {
        sym: 'get_documents_json(',
        isIndex: true,
        label: 'get_documents_json()',
        detail: '根据文档id获取文档json格式内容',
        insertText: 'get_documents_json()([${1:id1},${2:id2}])])',
        children: [
          {
            label: 'field(["字段1","字段2"])',
            detail: '提取json数组的指定字段',
            insertText: 'field(["${1:字段1}","${2:字段2}"])',
          }, {
            label: 'id',
            detail: '仅返回选中字段的数据',
            insertText: 'id',
          }, {
            label: 'title',
            detail: '仅返回选中字段的数据',
            insertText: 'title',
          }, {
            label: 'content',
            detail: '仅返回选中字段的数据',
            insertText: 'content',
          }, {
            label: 'score',
            detail: '仅返回选中字段的数据',
            insertText: 'score',
          },
        ],
      },  {
        label: 'current_token',
        detail: '获取当前执行流程的用户的身份',
        insertText: 'current_token' + COM_POS0,
      }, {
        sym: 'test',
        isIndex: true,
        label: 'test',
        detail: '测试模块专用变量',
        insertText: 'test',
        children: [
          {
            label: 'input',
            detail: '测试的input参数',
            insertText: 'input',
          }, {
            label: 'right_answer',
            detail: '参考的正确答案',
            insertText: 'right_answer',
          }, {
            label: 'answer',
            detail: '当前模型输出的答案',
            insertText: 'answer',
          }, {
            label: 'standard',
            detail: '测试评分标准',
            insertText: 'standard',
          },
        ],
      },
    ]
  }, {
    sym: 'role',
    isIndex: true,  // 索引触发，而非前缀匹配触发
    children: [
      {
        sym: 'input|开始',
        label: 'input/开始',
        isIndex: true,
        detail: '',
        insertText: 'input' + COM_POS0,
        children: [
          // {
          //   label: 'user_input',
          //   detail: '固定输入',
          //   insertText: 'user_input' + COM_POS0,
          // }, 
          {
            sym: '',
            label: '',
            detail: '自定义输入',
            type: 'start'
          }
        ]
      }, {
        sym: '',
        label: '',
        detail: '不可以直接使用，必须使用其中的方法或者属性',
        type: 'role',
        children: [
          {
            sym: 'var',
            label: 'var',
            detail: '角色自身变量输出',
            insertText: 'var' + COM_POS0,
            children: [
              {
                sym: '',
                label: '',
                detail: '',
                type: 'var'
              }
            ]
          }, {
            label: 'output',
            detail: '角色输出内容',
            insertText: 'output' + COM_POS0,
          }, {
            sym: '',
            label: '',
            detail: '工具返回值',
            type: 'tool'
          }
        ]
      }, {
        label: 'get_roles_outputs()',
        detail: '同时取多个角色的输出，并合并',
        insertText: 'get_roles_outputs([role1,role2...],field_key)' + COM_POS0,
      },
    ]
  }
];



onMounted(() => {
  setTimeout(() => {
    init();
  }, 70);
});
let etimer = null;
const init = (val) => {
  if (editorInstance) {
    editorInstance.dispose();
  }
  // "monaco-editor": "^0.43.0",
  if (!(monaco && monaco.editor)) {
    etimer = setTimeout(() => {
      init(val);
    }, 200);
    return false;
  }
  editorInstance = monaco.editor.create(editorContainer.value, {
    value: props.modelValue,
    language: props.language,
    contextmenu: false,
    quickSuggestions: false,
    // suggestOnTriggerCharacters:false,


    // wordWrap: props.wordWrap || "on",
    // wordWrapColumn: props.wordWrapColumn || 30,

    fontSize: props.fontSize || 14,
    fontFamily:
      "'Helvetica Neue', Helvetica, Tahoma, Arial, 'Microsoft YaHei', 'PingFang SC', 'Hiragino Sans GB', 'Heiti SC', 'WenQuanYi Micro Hei', sans-serif !important",
    lineNumbers: props.lineNumbers || "off",
    hover: false,
    minimap: {
      enabled: false, // 设置minimap不可用
    },
  });

  if (val) {
    editorInstance.setValue(val);
  }

  editorInstance.onDidFocusEditorText(() => {
    // 注册你的自动完成提供程序
    initLan();
  });

  editorInstance.onDidChangeModelContent((event) => {
    // 当文档内容改变时，这里的代码会被执行
    emits("update:modelValue", editorInstance.getValue());
  });
};

onBeforeUnmount(() => {
  clearTimeout(etimer);
  if (editorInstance) {
    editorInstance.dispose();
  }
});

const setValue = (val) => {
  emits("update:modelValue", val);
  init(val);
};
defineExpose({
  setValue,
});

const initLan = () => {
  if (monaco.languages.registerCompletionItemProvider[props.language]) {
    monaco.languages.registerCompletionItemProvider[props.language].dispose();
  }
  monaco.languages.registerCompletionItemProvider[props.language] =
    monaco.languages.registerCompletionItemProvider(props.language, {
      provideCompletionItems: (model, position, context, token) => {
        // 获取当前行数
        const line = position.lineNumber;
        // 获取当前列数
        const column = position.column;
        // 获取当前输入行的所有内容
        const content = model.getLineContent(line);
        let initContent = content;

        // 通过下标来获取当前光标后一个内容，即为刚输入的内容
        const sym = content[column - 2];

        let word = model.getWordUntilPosition(position);
        let range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn,
        };
        //---------------------------------------------------
        //上面的代码仅仅是为了获取sym，即提示符
        //---------------------------------------------------


        let nodes = []; // 深拷贝
        let edges = cloneDeep(props.edges); // 深拷贝
        let curnode = null;

        props.nodes.forEach((item) => {
          // 找到工作空间变量 添加进去
          if (item.data.type == "work_space" || item.data.type == "start") {
            nodes.push(item);
          }

          if (props.nodeid && item.id == props.nodeid) {
            curnode = item;
          }
        });





        function findConnectedNodesDFS(edges, nodeId) {
          const nodes = [];
          const visited = new Set(); // 记录已访问的节点
          const stack = [nodeId]; // 初始化栈，将起始节点 ID 压入栈中

          while (stack.length > 0) {
            const currentNodeId = stack.pop(); // 取出栈顶的节点 ID

            if (!visited.has(currentNodeId)) { // 如果该节点尚未被访问过
              visited.add(currentNodeId); // 标记该节点为已访问

              // 查找所有与当前节点相连的边
              for (const edge of edges) {
                if (edge.target === currentNodeId) { // 如果边的目标是当前节点
                  const sourceNode = edge.sourceNode;

                  // 检查节点的类型是否符合条件
                  if (sourceNode.data.type !== "start" && sourceNode.data.type !== "work_space") {

                    // 如果源节点尚未被访问过，则将其 ID 压入栈中
                    if (!visited.has(sourceNode.id)) {
                      nodes.push(sourceNode); // 将符合条件的节点添加到结果数组中
                      stack.push(sourceNode.id);
                    }
                  }
                }
              }
            }
          }

          return nodes;
        }



        if (props.nodeid) {

          nodes.push(...findConnectedNodesDFS(edges, props.nodeid));
        } else {
          nodes = cloneDeep(props.nodes);
        }

        let suggestions = [];




        word = model.getWordUntilPosition(position);
        range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: sym == ' ' ? word.startColumn - 1 : word.startColumn,   //替换空格插入
          endColumn: word.endColumn
        };
        console.log(range, word, sym == ' ')



        suggestions = [
          {
            label: 'log',
            kind: monaco.languages.CompletionItemKind.Function,
            insertText: 'log($1)$0', // $0表示最终光标位置
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            detail: "替换整个触发词(包括.)",
            range: range
          },
          // 更多补全项...
        ]

        suggestions = initSuggestions(model, position, nodes);
        console.log(suggestions)
        return {
          suggestions: suggestions,
        };
      },

      triggerCharacters: [".", "{", "%", " ", '"', "=", " ", "s", "n", "t", "w", "i", "f", "l"], // 触发提示的字符
    });
};



function initSuggestions(model, position, nodes) {
  // 获取当前行数
  const line = position.lineNumber;
  // 获取当前列数
  const column = position.column;
  // 获取当前输入行的所有内容
  const content = model.getLineContent(line);
  // 通过下标来获取当前光标后一个内容，即为刚输入的内容
  const sym = content[column - 2];



  console.log(model, position, line, column, content, sym)

  let word = model.getWordUntilPosition(position);
  let range = {
    startLineNumber: position.lineNumber,
    endLineNumber: position.lineNumber,
    startColumn: word.startColumn,
    endColumn: word.endColumn,
  };
  // 触发提示项
  let suggestions = [];
  if (sym == ' ' && content.length < 2) {
    // 如果是空格触发  并且是行首 触发代码块提示 
    range.startColumn = word.startColumn - 1;  //替换空格插入
    let arr = []; //根据关键词获取提示项
    COM_DICT.forEach((item) => {
      if (item.sym === sym) {
        arr = item.children;
      }
    })
    arr.forEach((item, index) => {
      suggestions.push({
        label: item.label,
        sortText: 'a' + index,

        insertText: item.insertText, // $0表示最终光标位置
        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
        detail: item.detail,
        range: range
      })
    })
  } else if (sym == '.') {
    // role.  或者 sys.

    let carrs = content.split(' ');  //用空格分割字符串 得到最后一段文本来做提示项的获取
    if (column > 1) {
      carrs = content.substring(0, column - 1).split(' ');
    }
    let cotents = carrs[carrs.length - 1].split('.');
    cotents.pop()
    let arr = getSugBysym(cloneDeep(nodes), cloneDeep(cotents));

    arr.forEach((item, index) => {
      if (item.sym === '') {
        // 特殊子节点 需要从node 获取子节点提示项
        let curnodes = getsubBynode(cloneDeep(nodes), item, cloneDeep(cotents))
        curnodes.forEach((item, cindex) => {
          suggestions.push({
            label: item.label,
            sortText: 'a' + cindex,
            insertText: item.insertText, // $0表示最终光标位置
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            detail: item.detail,
            range: range
          })
        })
      } else {

        suggestions.push({
          label: item.label,
          sortText: 'a' + index,
          insertText: item.insertText, // $0表示最终光标位置
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          detail: item.detail,
          range: range
        })
      }
    })
  }

  return suggestions;
}


function getsubBynode(nodes, sugdata, contents) {
  // 根据关键字从节点里获取提示项
  let type = sugdata.type;
  let arr = []
  // 获取子节点提示项
  if (type === 'role') {
    // 获取所有父节点 不包含开始节点 全局变量
    nodes.forEach((item) => {
      if (item.data.type != "work_space" && item.data.type != "start") {
        arr.push({
          sym: item.data.role,
          label: item.data.role,
          insertText: item.data.role + COM_POS0,
          detail: sugdata.detail,
        })
      }
    })
  } else if (type === 'tool') {
    // 获取节点下所有工具
    let curnode = getSugBysym(cloneDeep(nodes), cloneDeep(contents), undefined, true)
    console.log(curnode)
    if (curnode && curnode.data.functions && curnode.data.functions.length > 0) {
      let list = curnode.data.functions;
      for (let i = 0; i < list.length; i++) {
        let item = list[i]
        arr.push({
          sym: item.fun_name,
          label: item.fun_name,
          insertText: item.fun_name + COM_POS0,
          detail: item.name,
        })
      }
    }
  } else if (type === 'var') {
    // 获取自身变量
    let curnode = getSugBysym(cloneDeep(nodes), cloneDeep(contents), undefined, true)

    if (curnode && curnode.data.outputs && curnode.data.outputs.length > 0) {
      let list = []
      if (curnode.contents.length <= 1) {
        list = curnode.data.outputs
      } else {
        curnode.contents.shift()
        list = getSugByvar(cloneDeep(curnode.data.outputs), cloneDeep(curnode.contents))
      }
      for (let i = 0; i < list.length; i++) {
        let item = list[i]
        arr.push({
          sym: item.name,
          label: item.name,
          insertText: item.name + COM_POS0,
          detail: sugdata.detail,
        })
      }
    }
  } else if (type === 'start') {
    // 获取自身变量

    let curnode = getSugBysym(cloneDeep(nodes), cloneDeep(contents), undefined, true);

    if (curnode && curnode.data.inputs && curnode.data.inputs.length > 0) {
      let list = []
      if (curnode.contents.length < 1) {
        list = curnode.data.inputs
      } else {
        list = getSugByvar(cloneDeep(curnode.data.inputs), cloneDeep(curnode.contents))
      }
      for (let i = 0; i < list.length; i++) {
        let item = list[i]
        arr.push({
          sym: item.name,
          label: item.name,
          insertText: item.name + COM_POS0,
          detail: sugdata.detail,
        })
      }
    }
  } else if (type === 'space') {
    let curnode = null
    nodes.forEach((item) => {
      if (item.data.type == "work_space") {
        // 找到节点  
        curnode = item;
      }
    });


    if (curnode && curnode.data.space_vars && curnode.data.space_vars.length > 0) {
      let list = curnode.data.space_vars
      for (let i = 0; i < list.length; i++) {
        let item = list[i]
        arr.push({
          sym: item.name,
          label: item.name,
          insertText: item.name + COM_POS0,
          detail: sugdata.detail,
        })
      }
    }

  }
  return arr;
}

function getSugByvar(list, contents, childs) {


  let curcontent = contents[0];  //从第0个输入开始匹配
  let arr = []

  if (curcontent === '' || curcontent === undefined) {
    // 如果是空字符串 直接出栈 进行下一层匹配
    contents.shift();
    if (contents.length < 1) {
      // 如果没有了
      return childs || [];
    }
    return getSugByvar(list, contents, childs);
  }
  for (let i = 0; i < list.length; i++) {
    let item = list[i];
    if (item.name === curcontent) {
      // 找到了 出栈
      contents.shift();
      if (contents.length < 1) {
        // 如果数组已经为空 则返回当前节点提示项
        arr = item.children || [];
        return arr;
      } else {
        // 继续查询后续待查找字符
        let curchilds = item.children || []
        arr = getSugByvar(curchilds, contents, curchilds)
      }
    }
  }
  return arr;
}




function getSugBysym(nodes, contents, childs, isGetNodes) {
  let curcontent = contents[0];  //从第0个输入开始匹配
  let children = childs || COM_DICT;
  let arr = []
  let findNodes = null;

  if (curcontent === '' || curcontent === undefined) {
    // 如果是空字符串 直接出栈 进行下一层匹配
    contents.shift();
    if (contents.length < 1) {
      // 如果没有了
      return childs || [];
    }
    return getSugBysym(cloneDeep(nodes), contents, childs, isGetNodes);
  }
  for (let i = 0; i < children.length; i++) {
    let item = children[i];
    if (item.sym === '') {
      // 如果是空字符串 需要从节点获取是否存在
      if (item.type === 'role') {
        // 遍历节点  获取对应的节点字段
        nodes.forEach((item) => {
          if (item.data.type != "work_space" && item.data.type != "start") {
            if (item.data.role === curcontent) {
              // 找到节点  
              findNodes = item;
            }
          }
        });

      } else if (item.type === 'start') {
        // 获取开始节点inputs 变量
        nodes.forEach((item) => {
          if (item.data.type == "start") {
            // 找到节点  
            findNodes = item;
          }
        });
      }

      if (findNodes) {

        // 找到了节点 直接返回子节点提示项
        contents.shift();  //把已找到的从数组中移除

        if (isGetNodes) {
          // 如果是获取节点 则直接返回当前节点
          findNodes.contents = contents;
          return findNodes;
        }
        if (contents.length < 1) {
          // 如果数组已经为空 则返回开始节点提示项

          arr = item.children;
        } else {
          // 继续查询后续待查找字符
          arr = getSugBysym(cloneDeep(nodes), contents, item.children, isGetNodes)
        }


      }

    } else if (item.sym) {
      let syms = item.sym.split('|');
      let cindex = -1
      for (let i = 0; i < syms.length; i++) {
        let cursym = syms[i]
        if (cursym === curcontent || (item.isIndex && curcontent.indexOf(cursym) !== -1)) {
          // isIndex 表示是否模糊匹配 比如 sys.role.name  这里的name 就是模糊匹配 比如 sys.role.na 也能匹配到name

          cindex = i;
        }
      }

      if (cindex !== -1) {
        // 如果 找到了 并且后面还有待查找的字符串 则继续递归查询子节点提示项
        contents.shift();  //把已找到的从数组中移除

        if (isGetNodes && item.sym === 'input|开始') {
          // 如果是获取节点 并且查询到了开始节点  返回开始节点
          nodes.forEach((citem) => {
            if (citem.data.type == "start") {
              // 找到节点  
              findNodes = citem;
            }
          });
          findNodes.contents = contents;
          return findNodes;
        }
        if (contents.length < 1) {
          // 如果数组已经为空 则返回当前节点提示项
          arr = item.children;
        } else {
          // 继续查询后续待查找字符

          if (item.sym === 'var' || item.sym === 'input|开始') {
            // 处理所有的变量 需要从节点递归  这里不继续查找
            arr = item.children;
          } else {
            arr = getSugBysym(cloneDeep(nodes), contents, item.children, isGetNodes)
          }

        }
      }

    }
  }


  return arr;
}


function findNodeByName(tree, path) {
  let currentNode = tree;
  for (let i = 0; i < path.length; i++) {
    const child = currentNode.children.find((node) => node.name === path[i]);
    if (!child) {
      return null;
    }
    currentNode = child;
  }
  return currentNode;
}
const getNodesChild = (node, vals) => {
  let arr = [];
  if (node.data.type == "start") {
    // 获取开始节点参数
    let childs = null;
    if (node.data.inputs) {
      node.data.inputs.forEach((item) => {
        if (!vals || vals.length < 2) {
          // 获取所有参数
          arr.push({ label: item.name, insertText: item.name });
        } else {
          // 获取多级
          let curvals = cloneDeep(vals);
          curvals.shift();
          childs = findNodeByName({ children: node.data.inputs }, curvals);
        }
      });
    }
    if (childs && childs.children) {
      childs.children.forEach((child) => {
        arr.push({ label: child.name, insertText: child.name });
      });
    }
  } else if (node.data.type == "work_space") {
    // 获取工作空间节点变量
    if (!vals || vals.length < 2) {
      arr = [
        {
          label: "get_document()",
          insertText: "get_document()",
          kind: 1,
          detail: "全局函数",
        },
        {
          label: "get_talks()",
          insertText: "get_talks()",
          kind: 1,
          detail: "全局函数",
        },
        {
          label: "get_talks_from()",
          insertText: "get_talks_from()",
          kind: 1,
          detail: "全局函数",
        },
        {
          label: "get_talks_to()",
          insertText: "get_talks_to()",
          kind: 1,
          detail: "全局函数",
        },
        {
          label: "get_talks_from_to()",
          insertText: "get_talks_from_to()",
          kind: 1,
          detail: "全局函数",
        },
      ];
    }
    if (node.data.space_vars) {
      node.data.space_vars.forEach((item) => {
        if (!vals || vals.length < 2) {
          arr.push({ label: item.name, insertText: item.name });
        }
      });
    }
  } else if (node.data.type == "llm" || node.data.type == "loop") {
    // 获取大模型变量
    let childs = null;
    if (node.data.outputs && vals && vals.length >= 2 && vals[1] == "output") {
      node.data.outputs.forEach((item) => {
        if (vals.length < 3) {
          // 获取所有参数
          arr.push({ label: item.name, insertText: item.name });
        } else {
          // 获取多级
          let curvals = cloneDeep(vals);
          curvals.shift();
          curvals.shift();
          childs = findNodeByName({ children: node.data.outputs }, curvals);
        }
      });
    }
    if (childs && childs.children) {
      childs.children.forEach((child) => {
        arr.push({ label: child.name, insertText: child.name });
      });
    }
    if ((!vals || vals.length < 2)) {
      // 所有节点都有output
      arr.push(
        { label: "output", insertText: "output" }
      );
    }
    if ((!vals || vals.length < 2) && node.data.functions) {
      // 获取functions

      arr.push(
        { label: "react", insertText: "react" },
        { label: "variables", insertText: "variables" },
        { label: "exist()", insertText: "exist()", kind: 1, detail: "全局函数" },
      );

      node.data.functions.forEach((item) => {
        arr.push({ label: item.fun_name, insertText: item.fun_name, kind: 5 });
      });
    }
  } else if (node.data.type == "sys") {
    arr = [
      {
        label: "time()",
        insertText: "time()",
        kind: 1, detail: "全局函数"
      },
    ];
  }
  return arr;
};

//
// editor.updateOptions({ lineNumbers: false }); // 隐藏行号
// // 或者
// editor.updateOptions({ lineNumbers: true }); // 显示行号
</script>
<template>
  <div class="editor-containbox nodrag nowheel">
    <div ref="editorContainer" class="editor-container c-scroll-contain"></div>
  </div>
</template>
<style scoped>
.editor-containbox:deep(.monaco-editor .view-overlays .current-line) {
  border: none !important;
}

.editor-containbox:deep(.mtk1) {
  color: #606266;
}

.editor-containbox:deep(.monaco-editor .scroll-decoration) {
  box-shadow: none !important;
}

.editor-containbox:deep(canvas.decorationsOverviewRuler) {
  opacity: 0;
}

.editor-containbox:deep(.monaco-editor .view-line) {
  padding-left: 5px !important;
  box-sizing: border-box;
}

.editor-containbox {
  display: block;
  width: 100%;
  height: 100%;
  position: relative;
  padding: 5px 0;
  box-sizing: border-box;
  border: 1px solid var(--el-border-color);
  border-radius: 5px;
  z-index: 11;
}

.editor-container {
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  text-align: left;
  font-size: 12px;
  position: relative;
  z-index: 1;
}
</style>