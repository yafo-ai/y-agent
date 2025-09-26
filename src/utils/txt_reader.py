def read_file_with_different_encodings(file_path):
    encodings = ['utf-8', 'gbk', 'gb2312', 'ascii', 'iso-8859-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
                print(f"编码方式 {encoding} 读取成功")
                return content
        except UnicodeDecodeError:
            print(f"编码方式 {encoding} 读取失败")
    return None