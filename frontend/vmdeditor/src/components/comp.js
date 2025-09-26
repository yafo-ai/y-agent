



export function goback(path, router, fpath = '/') {
  if (path) {
    router.push(path);
    return;
  }

  if (window.history?.state?.back) {
    router.go(-1);
  } else {
    router.push(fpath);
  }
}

export function getTime(time) {
  if (!time) return "";
  time = time.replace("T", " ");
  time = time.split(".")[0];
  return time;
};

export function copyToClipboard(text,hideTips) {
  const textarea = document.createElement('textarea');
  textarea.value = text;
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand('copy');
  document.body.removeChild(textarea);
  if(!hideTips){
    window._this.$toast('复制成功')
  }
  
}