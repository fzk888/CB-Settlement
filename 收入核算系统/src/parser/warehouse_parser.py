def _extract_total_amount_from_pdf(self, file_path: str) -> Decimal:
        """从PDF中提取Total Amount金额"""
        try:
            # 首先尝试使用pdfplumber（更准确）
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        # 查找Total Amount行
                        lines = text.split('\n')
                        for line in lines:
                            if 'total amount' in line.lower():
                                # 提取金额数字
                                # 支持格式如: "Total Amount: USD 4,770.06"
                                match = re.search(r'[\d,]+\.?\d*', line)
                                if match:
                                    amount_str = match.group().replace(',', '').replace('.', '', 1)  # 先替换逗号，再替换第一个点
                                    return Decimal(amount_str)
            
            # 如果pdfplumber失败，尝试PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        lines = text.split('\n')
                        for line in lines:
                            if 'total amount' in line.lower():
                                match = re.search(r'[\d,]+\.?\d*', line)
                                if match:
                                    amount_str = match.group().replace(',', '').replace('.', '', 1)  # 先替换逗号，再替换第一个点
                                    return Decimal(amount_str)
            
            return None
            
        except Exception as e:
            print(f"  PDF提取失败: {e}")
            return None