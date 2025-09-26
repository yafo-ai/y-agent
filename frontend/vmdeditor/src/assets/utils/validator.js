function validByPhone(phone) {
  // 校验手机号
  const myreg = /^[1][3,4,5,6,7,8,9][0-9]{9}$/;
  if (!myreg.test(phone)) {
    return false;
  }
  return true;
}
function validByTel(value) {
  // 校验手机固定电话
  const isPhone = /^(0[0-9]{2,3}[-|\s]?)?[0-9]{7,8}$/;
  // let isPhone = /^((0\d{2,3})-)(\d{7,8})(-(\d{3,}))?$/;
  const isMob = /^[1][3,4,5,6,7,8,9][0-9]{9}$/;
  if (isMob.test(value) || isPhone.test(value)) {
    return true;
  }

  return false;
}

function validByBankNo(value) {
  // 校验银行卡号
  const isBankNo = /^\d{13,19}$/;
  if (isBankNo.test(value)) {
    return true;
  }


  return false;
}


function validByEmail(email) {
  // 判断用户输入的电子邮箱格式是否正确
  const myreg = /^[a-zA-Z0-9_-]+@([a-zA-Z0-9_-]+\.)+(com|cn|net|org)$/;
  if (!myreg.test(email)) {
    return false;
  }
  return true;
}

function validByName(name) {
  // 校验手机号
  const myreg = /^[1][1,2,3,4,5,6,7,8,9,0][0-9]{9}$/;
  if (!myreg.test(name)) {
    return false;
  }
  return true;
}

function validByPersonNo(name) {
  // 纳税人识别号
  /*eslint-disable*/ 
  const myreg =  /^([0-9A-Za-z]{15}|[0-9A-Za-z]{17}|[0-9A-Za-z]{18}|[0-9A-Za-z]{20})$/
  /* eslint-enable */
  if (!myreg.test(name)) {
    return false;
  }
  return true;
}




function isValidVariableName(name) {
  // 校验变量名
  const regex = /^[a-zA-Z_][a-zA-Z0-9_]*$/;
  return regex.test(name);
}

function isValidJSON(text) {
  try {
      JSON.parse(text);
      return true;
  } catch (error) {
      return false;
  }
}

function isInteger(str) {
  return /^-?\d+$/.test(str);
}
function isValidNumber(str) {
  return /^[\d.]+$/.test(str); // 匹配数字和点
}
function isArray(input) {
  return Array.isArray(input);
}

function validateUrl(url) {
  console.log(url);
  let regex = /^(https?|ftp):\/\/[^\s/$.?#].[^\s]*$/i;
  return regex.test(url);
}

function validateString(str) {
  // 正则表达式匹配以下特殊符号：
  // !@#$%^&*()-_+=[]{}|\;:'",./<>?
  const specialChars = /[\s!@#$%^&*()\-。，；‘’+=\[\]{}|\\;:'",./<>?]/;
  return specialChars.test(str);
}
function isValidateName(name) {
  // 校验变量名
  const regex = /^[a-z_]*$/;
  return regex.test(name);
}
export {
  isValidateName,
  validateString,
  validateUrl,
  isValidNumber,
  isInteger,
  isValidJSON,
  isArray,
  isValidVariableName,
  validByPhone,
  validByName,
  validByEmail,
  validByTel,
  validByBankNo,
  validByPersonNo,
};
