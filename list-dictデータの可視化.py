#-*- coding:utf-8 -*-
import wx,sys,os
import  wx.grid as gridlib
import wx.lib.scrolledpanel as scrolled
import datetime

# 文字の入力
def input_dialog(title:str ="入力ダイアログ",message:str ="文字を入力してください")->str:
    dlg = wx.TextEntryDialog(parent=None, message=message, caption=title,
                value="",
                style= wx.OK | wx.STAY_ON_TOP #|wx.TE_MULTILINE
                )
    dlg.ShowModal()
    dlg.Destroy()

    return dlg.GetValue()

# 保存先フォルダを選択
def path():
    #app=wx.App()
    wx.MessageBox('保存先フォルダを選択してください','フォルダ選択',wx.STAY_ON_TOP)
    # フォルダ選択ダイアログを作成
    folda = wx.DirDialog(None,style=wx.DD_CHANGE_DIR | wx.OK | wx.STAY_ON_TOP,message="保存先フォルダ")
    # フォルダが選択されたとき
    if folda.ShowModal() == wx.ID_OK:
        folda_path = folda.GetPath()
        folda.Destroy()
        return folda_path

filetype = """\
     TXTfiles(*.txt)|*.txt|
     Picklefiles(*.pickle)|*.pickle|
     zfiles(*.z)|*.z|
     gzfiles(*.gz)|*.gz|
     bz2files(*.bz2)|*.bz2|
     xzfiles(*.xz)|*.xz|
     lzmafiles(*.lzma)|*.lzma|
     All file(*)|*"""

# ファイルの選択
def open_file():
    with wx.FileDialog(None, u'対象のファイル選択してください', style=wx.FD_OPEN |wx.FD_FILE_MUST_EXIST) as dialog:
        dialog.SetWildcard(filetype)
        # ファイルが選択されたとき
        if dialog.ShowModal() == wx.ID_OK:
            # 選択したファイルパスを取得する
            return dialog.GetPath()

# ファイルの選択
def save_file():
    with wx.FileDialog(None, u'データを保存します', style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dialog:
        dialog.SetWildcard(filetype)
        # ファイルが選択されたとき
        if dialog.ShowModal() == wx.ID_OK:
            return dialog.GetPath()
#-------------------------------------------------------------------------------
def choice_datatype(item):
    if type(item) == str:
        return gridlib.GRID_VALUE_STRING
    elif type(item) == bool:
        return gridlib.GRID_VALUE_BOOL
    elif type(item) == int:
        return gridlib.GRID_VALUE_NUMBER
    elif type(item) == float:
        return gridlib.GRID_VALUE_FLOAT
    elif type(item) == datetime.datetime:
        return gridlib.GRID_VALUE_DATETIME
    elif type(item) == datetime.date:
        return gridlib.GRID_VALUE_DATE
    else:
        return gridlib.GRID_VALUE_TEXT

class GridResizable:
    """
    ↓参照
    http://wxpython-users.1045709.n5.nabble.com/wxGrid-reload-table-td2311585.html
    """
    def __init__(self):
        # The resizable grid needs to remeber how big it was
        # in order to send appropriate events to add and remove
        # columns
        self._cols = self.GetNumberCols()
        self._rows = self.GetNumberRows()
       
    def ResetView(self, grid):
        grid.BeginBatch()
        for current, new, delmsg, addmsg in [
            (self._rows, self.GetNumberRows(), gridlib.GRIDTABLE_NOTIFY_ROWS_DELETED,
            gridlib.GRIDTABLE_NOTIFY_ROWS_APPENDED),
            (self._cols, self.GetNumberCols(), gridlib.GRIDTABLE_NOTIFY_COLS_DELETED,
            gridlib.GRIDTABLE_NOTIFY_COLS_APPENDED),
            ]:
            if new < current:
                msg = gridlib.GridTableMessage(self,delmsg,new,current-new)
                grid.ProcessTableMessage(msg)
            elif new > current:
                msg = gridlib.GridTableMessage(self,addmsg,new-current)
                grid.ProcessTableMessage(msg)
        self.UpdateValues(grid)
        grid.EndBatch()
        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()
        # XXX
        # Okay, this is really stupid, we need to "jiggle" the size
        # to get the scrollbars to recalibrate when the underlying
        # grid changes.
        h,w = grid.GetSize()
        grid.SetSize((h+1, w))
        grid.SetSize((h, w))
        grid.ForceRefresh()
        self.UpdateValues(grid)
       
    def UpdateValues(self, grid):
        """Update all displayed values without changing the grid size"""
        msg = gridlib.GridTableMessage(self, gridlib.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        grid.ProcessTableMessage(msg)


class CustomDataTable(gridlib.GridTableBase, GridResizable):
    def __init__(self, path, data, header, index):
        super().__init__()
                
        self.data = data
        self.colLabels = header
        self.rowLabels = index

        self.dataTypes = []
        for i in data[0]:
            self.dataTypes.append(choice_datatype(i))

        GridResizable.__init__(self)

    def GetNumberRows(self):
        return len(self.data) 

    def GetNumberCols(self):
        return len(self.data[0])

    def IsEmptyCell(self, row, col):
        try:
            return not self.data[row][col]
        except IndexError:
            return True

    def GetValue(self, row, col):
        try:
            return self.data[row][col]
        except IndexError:
            return ''

    def SetValue(self, row, col, value):
        def innerSetValue(row, col, value):
            try:
                self.data[row][col] = value
            except IndexError:
                pass
#                self.data.append([''] * self.GetNumberCols())
#                innerSetValue(row, col, value)
#                msg = gridlib.GridTableMessage(self,
#                        gridlib.GRIDTABLE_NOTIFY_ROWS_APPENDED, 1)

#                self.GetView().ProcessTableMessage(msg)
        innerSetValue(row, col, value) 

    def GetColLabelValue(self, col):
        return self.colLabels[col]

    def GetRowLabelValue(self, row):
        return self.rowLabels[row]

    def GetTypeName(self, row, col):
        return self.dataTypes[col]

    def CanGetValueAs(self, row, col, typeName):
        colType = self.dataTypes[col].split(':')[0]
        if typeName == colType:
            return True
        else:
            return False

    def CanSetValueAs(self, row, col, typeName):
        return self.CanGetValueAs(row, col, typeName)
    # --------------------------------------------------------------------------
    # 要素の追加や削除
    def DeleteCols(self, pos, numCols=1):
        try:
            for i in range(numCols):
                for j in range(len(self.data)):
                    del self.data[j][pos]
                del self.colLabels[pos],self.dataTypes[pos]
                
            return True
        except:
            return False

    def DeleteRows(self, pos, numRows=1):
        try:
            for i in range(numRows):
                del self.data[pos],self.rowLabels[pos]

            return True
        except:
            return False

    def InsertCols(self, pos=None,numCols=1):
        try:
            for i in range(numCols):
                for j in range(len(self.data)):
                    self.data[j].insert(pos,"")
                    """
                    if pos != None:
                        self.data[j].insert(pos,"")
                    else:
                        self.data[j].append("")
                    """
                self.colLabels.append("new col")
                self.dataTypes.append(gridlib.GRID_VALUE_TEXT)

            return True
        except:
            return False

    def InsertRows(self, pos=None,numRows=1):
        try:
            for i in range(numRows):
                append_row = []
        
                for types in self.dataTypes:
                    if types == gridlib.GRID_VALUE_STRING:
                        d = ""
                    elif types == gridlib.GRID_VALUE_BOOL:
                        d = False
                    elif types == gridlib.GRID_VALUE_NUMBER:
                        d = 0
                    elif types == ridlib.GRID_VALUE_FLOAT:
                        d = 0.0
                    elif types == gridlib.GRID_VALUE_DATETIME:
                        d = datetime.datetime.now()
                    elif types == gridlib.GRID_VALUE_DATE:
                        d = datetime.date.today()
                    else:
                        d = ""

                    append_row.insert(pos,d)
                    """
                    if pos != None:
                        append_row.insert(pos,d)
                    else:
                        append_row.append(d)
                    """

                self.data.append(append_row)
                self.rowLabels.append(str(len(self.data)-1))

            return True
        except:
            return False

    def AppendCols(self,numCols=1):
        return self.InsertCols(numCols=numCols)

    def AppendRows(self,numRows=1):
        return self.InsertRows(numRows=numRows)
    # --------------------------------------------------------------------------
    # ラベル名の編集
    def SetColLabelValue(self, col, label):
        self.colLabels[col] = label

    def SetRowLabelValue(self, row, label):
        self.rowLabels[row] = label

class CustTableGrid(gridlib.Grid):
    def __init__(self, parent ,filepath,index_axis):

        ext = os.path.splitext(filepath)[-1]
        if ext == ".pickle":
            import pickle
            with open(filepath,mode="rb") as f:
                self.data = pickle.load(f)
        elif ext == ".txt":
            import ast,codecs
            with codecs.open(filepath,mode="r",encoding="utf-8",errors="backslashreplace") as f:
                self.data = ast.literal_eval(f.read())
        elif ext in (".z",".gz",".bz2",".xz",".lzma"):
            import joblib
            self.data = joblib.load(filepath)
            
        header = list(self.data[0].keys())
        for row in self.data[1:]:
            if len(header) < len(row.keys()):
                header = list(row.keys())
            
            
        index  = []
        data_list = []
        for row in self.data:
            cols = []
            # データ本体の処理
            for col in header:
                try:
                    cols.append(row[col])
                except:
                    cols.append("")
            data_list.append(cols)
            # インデックス処理
            try:
                index.append(row[index_axis])
            except KeyError:
                index.append("")
        #print(len(self.data_list))
        
        gridlib.Grid.__init__(self, parent, -1)

        table = CustomDataTable(path, data_list, header, index)
        self.SetTable(table, True)
        self.AutoSize()

    # --------------------------------------------------------------------------
    # 要素の追加や削除
    def DeleteCols(self, pos, numCols=1):
        super().DeleteCols(pos=pos, numCols = numCols)
        self.GetTable().ResetView(self)
        
    def DeleteRows(self, pos, numRows=1):
        super().DeleteRows(pos=pos, numRows = numRows)
        self.GetTable().ResetView(self)

    def PopCols(self,numCols=1):
        self.DeleteCols(pos = self.GetTable().GetNumberCols()-1, numCols = numCols)
        self.GetTable().ResetView(self)

    def PopRows(self,numRows=1):
        self.DeleteRows(pos = self.GetTable().GetNumberRows()-1, numRows = numRows)
        self.GetTable().ResetView(self)
        
    def InsertCols(self, pos, numCols=1):
        super().InsertCols(pos = pos, numCols = numCols)
        self.GetTable().ResetView(self)
        
    def InsertRows(self, pos, numRows=1):
        super().InsertRows(pos = pos, numRows = numRows)
        self.GetTable().ResetView(self)
        
    def AppendCols(self,numCols=1):
        self.InsertCols(pos = self.GetTable().GetNumberCols(), numCols = numCols)
        self.GetTable().ResetView(self)
        
    def AppendRows(self,numRows=1):
        self.InsertRows(pos = self.GetTable().GetNumberRows(), numRows = numRows)
        self.GetTable().ResetView(self)
    # --------------------------------------------------------------------------
    # ラベル名の編集
    def SetColLabelValue(self, col, value):
        super().SetColLabelValue(col, value)
        self.GetTable().ResetView(self)

    def SetRowLabelValue(self, row, value):
        super().SetRowLabelValue(row, value)
        self.GetTable().ResetView(self)
     
#-------------------------------------------------------------------------------
filepath = ""
def main(fpath:str,index_axis:str):
    global filepath
    filepath = fpath
    #---------------------------------------------------------------------------
    def backup_data(event):
        if event == wx.grid.EVT_GRID_CELL_CHANGING:
            data = []
            import ast
            for row in range(grid.GetNumberRows()):
                data.append({grid.GetColLabelValue(col):ast.literal_eval(grid.GetCellValue(row,col)) for col in range(grid.GetNumberCols())})
            grid.data = data
            print(data)
    #---------------------------------------------------------------------------
    def reset():
        for i in range(grid.GetNumberRows()-1):
            grid.PopRows()
        for i in range(grid.GetNumberCols()-1):
            grid.PopCols()
        grid.SetCellValue(0,0,"")
        grid.SetRowLabelValue(0,"")
        grid.SetColLabelValue(0,"")        
    #---------------------------------------------------------------------------
    def status_update(event):
        frame.SetStatusText('{0}行目{1}列目のセルを選択中：{2}'.format(
                grid.GetGridCursorRow()+1,
                grid.GetGridCursorCol()+1,
                filepath
                ))
    #---------------------------------------------------------------------------
    def selectMenu(event):
        if event.GetId() in (1,2):
            data = []
            import ast
            for row in range(grid.GetNumberRows()):
                cols = {}
                for col in range(grid.GetNumberCols()):
                    try:
                        cols[grid.GetColLabelValue(col)] = ast.literal_eval(grid.GetCellValue(row,col))
                    except (ValueError,SyntaxError):
                        cols[grid.GetColLabelValue(col)] = grid.GetCellValue(row,col)
                data.append(cols)

            if event.GetId() == 1:
                global filepath
                filepath = save_file()
                if filepath == None:
                    frame.SetStatusText(f'保存をキャンセルしました')
                    return
                #filepath = os.path.join(path(),input_dialog(message="ファイル名を入力してください"))
                ext = os.path.splitext(filepath)[-1]
                if ext == ".pickle":
                    import pickle
                    with open(filepath,mode="wb") as f:
                        pickle.dump(data,f)
                elif ext in (".z",".gz",".bz2",".xz",".lzma"):
                    import joblib
                    joblib.dump(data,filepath,compress=3)
                else:
                    import pprint
                    with open(filepath,mode="w",encoding="utf-8") as f:
                        pprint.pprint(data,f)
            elif event.GetId() == 2:
                ext = os.path.splitext(filepath)[-1]
                if ext == ".pickle":
                    import pickle
                    with open(filepath,mode="wb") as f:
                        pickle.dump(data,f)
                elif ext == ".txt":
                    import pprint
                    with open(filepath,mode="w",encoding="utf-8") as f:
                        pprint.pprint(data,f)
                elif ext in (".z",".gz",".bz2",".xz",".lzma"):
                    import joblib
                    joblib.dump(data,filepath,compress=3)
            grid.data = data
        elif event.GetId() in (3,4):
            data = []
            for row in range(grid.GetNumberRows()):
                data.append({grid.GetColLabelValue(col):grid.GetCellValue(row,col) for col in range(grid.GetNumberCols())})
            filepath = save_file()
            if filepath == None:
                frame.SetStatusText(f'保存をキャンセルしました')
                return
            import pandas as pd
            data = pd.DataFrame(data)
            if event.GetId() == 3:
                data.to_csv(filepath)
            elif event.GetId() == 4:
                data.to_tsv(filepath)
        #---------------------------------------------------------------------------    
        else:
            # 最後尾に1列追加する
            if event.GetId() == 5:
                grid.AppendCols()
            # 最後尾に1行追加する
            elif event.GetId() == 6:
                grid.AppendRows()
            # 現在選択中の1列を削除する
            elif event.GetId() == 7:
                grid.DeleteCols(pos=grid.GetGridCursorCol())
            # 現在選択中の1行を削除する
            elif event.GetId() == 8:
                grid.DeleteRows(pos=grid.GetGridCursorRow())
            # 最後尾の1列を削除する
            elif event.GetId() == 9:
                grid.PopCols()
            # 最後尾の1行を削除する
            elif event.GetId() == 10:
                grid.PopRows()

            # 現在選択中の列のラベル名を変更する
            elif event.GetId() == 11:
                col = grid.GetSelectedCols()
                if len(col) == 0:
                    return
                else:
                    col = col[0]
                    word = input_dialog(message="列ラベル名編集")
                    if word:
                        #grid.SetColLabelValue(grid.GetGridCursorCol(),word)
                        grid.SetColLabelValue(col,word)
                    else:
                        return
            # 現在選択中の行のラベル名を変更する
            elif event.GetId() == 12:
                word = input_dialog(message="行ラベル名編集")
                if word:
                    grid.SetRowLabelValue(grid.GetGridCursorRow(),word)
                else:
                    return
            # 元（変更一個前）に戻す
            elif event.GetId() == 13:
                reset()
                # データの取得
                header = list(grid.data[0].keys())
                index = [grid.data[0][index_axis]]
                for row in grid.data[1:]:
                    if len(header) < len(row.keys()):
                        header = list(row.keys())
                    try:
                        index.append(row[index_axis])
                    except KeyError:
                        index.append("")
                # 最初の一マス目を入力
                grid.SetCellValue(0,0,grid.data[0][header[0]])
                grid.SetRowLabelValue(0,index[0])
                grid.SetColLabelValue(0,header[0])  
                # 行と列の作成
                for row,label in enumerate(index):
                    if row == 0:
                        continue
                    grid.AppendRows()
                    grid.SetRowLabelValue(row,label)
                for col,head in enumerate(header):
                    if col == 0:
                        continue
                    grid.AppendCols()
                    grid.SetColLabelValue(col,head)
                # 一マスごとデータ入力
                for row,label in enumerate(index):
                    for col,head in enumerate(header):
                        try:
                            #print(row,col,str(grid.data[row][head]))
                            grid.SetCellValue(row,col,str(grid.data[row][head]))
                        except KeyError:
                            grid.SetCellValue(row,col,"")
            # 全要素削除して一マスの表にする
            elif event.GetId() == 14:
                reset()
            grid.AutoSize()
        
    #---------------------------------------------------------------------------    
    # GUIの作成
    frame       = wx.Frame(None, wx.ID_ANY, 'テストフレーム', size=(1000, 500))
    panel = wx.Panel(frame,wx.ID_ANY) # Panelの作成
    grid = CustTableGrid(panel ,filepath ,index_axis)
    layout = wx.BoxSizer(wx.HORIZONTAL)
    layout.Add(grid)
    panel.SetSizer(layout)
    panel.Fit()
    
    menu_file = wx.Menu()
    menu_file.Append(1, '新規保存')
    menu_file.Append(2, '上書き保存')
    menu_file.Append(3, 'csv出力')
    menu_file.Append(4, 'tsv出力')
 
    menu_edit = wx.Menu()
    menu_edit.Append(5,'最後尾に1列追加する')
    menu_edit.Append(6,'最後尾に1行追加する')
    menu_edit.Append(7,'現在選択中の1列を削除する')
    menu_edit.Append(8,'現在選択中の1行を削除する')
    menu_edit.Append(9,'最後尾の1列を削除する')
    menu_edit.Append(10,'最後尾の1行を削除する')
    menu_edit.Append(11,'現在選択中の列のラベル名を変更する')
    menu_edit.Append(12,'現在選択中の行のラベル名を変更する')
    menu_edit.Append(13,'Undo')
    menu_edit.Append(14,'All Delete')
 
    menu_bar = wx.MenuBar()
    menu_bar.Append(menu_file, 'ファイル')
    menu_bar.Append(menu_edit, '編集')

    frame.Bind(wx.EVT_MENU,selectMenu)
    frame.SetMenuBar(menu_bar)

    frame.CreateStatusBar()
    frame.SetStatusText(f'read {filepath}')
    # ステータスバーを常時更新
    timer = wx.Timer(frame)
    frame.Bind(wx.EVT_TIMER, status_update)
    timer.Start(100) # 0.1s
    #frame.Bind(wx.EVT_CHAR,status_update)

    #frame.Bind(wx.grid.EVT_GRID_SELECT_CELL, status_update)
    #frame.Bind(wx.EVT_GRID_CELL_CHANGED, grid.)
    frame.Bind(wx.grid.EVT_GRID_CELL_CHANGING, backup_data)

    # 可視化
    frame.Show()
    application.MainLoop()
    
if __name__ == "__main__":
    application = wx.App()
    main(open_file(),input_dialog(message="indexにする列名を入力してください"))
else:
    application = wx.App()
    main(sys.argv[1],sys.argv[2])
