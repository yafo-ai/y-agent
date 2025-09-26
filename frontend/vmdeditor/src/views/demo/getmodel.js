
// 获取Modeler详情
export function getModelerDetail(modelId) {
  // TODO
  return new Promise((resolve) => {
    resolve({
      msg: "操作成功",
      code: 200,
      data: {
        id: "a61cf7f1-e3a1-11ee-aa21-aed1b8855c31",
        key: "leave",
        name: "请假",
        metaInfo: '{"name":"请假","revision":1,"description":null}',
        bpmnXml:
          '',
      },
    });
  });
}

// 部署模型
export function updateModeler(data) {
  // TODO
  return new Promise((resolve) => {
    resolve({
      code: 200,
      msg: "成功！",
    });
  });
}
