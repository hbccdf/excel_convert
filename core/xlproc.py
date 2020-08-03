
import math
import xlrd

printer = print


class Coor:
    def __init__(self, r, c):
        self.r = r
        self.c = c

        self.calpha = ctoa(c)
        self.ralpha = f'{r+1}'
        self.rc = f'{self.ralpha}{self.calpha}'


def log(msg):
    if callable(printer):
        printer(msg)


def celltoa(r: int, c: int):
    if c < 26:
        return chr(c + 65)

    n1 = math.floor(c / 26) - 1
    n2 = c % 26

    return f'{r+1}{chr(n1 + 65) + chr(n2 + 65)}'


def ctoa(c: int):
    if c < 26:
        return chr(c + 65)

    n1 = math.floor(c / 26) - 1
    n2 = c % 26

    return chr(n1 + 65) + chr(n2 + 65)


def column2alpha(column_num):

    if column_num < 26:
        return chr(column_num + 65)

    n1 = math.floor(column_num / 26) - 1
    n2 = column_num % 26

    return chr(n1 + 65) + chr(n2 + 65)


def trim(s):
    if isinstance(s, str):
        s = s.strip()
        if s == '':
            return None
    return s


def array2d(sheet: xlrd.sheet.Sheet):
    return [
        [cell.value for cell in row]
        for row in sheet.get_rows()
    ]


def array2d_transpose(sheet: xlrd.sheet.Sheet):
    a2d = array2d(sheet)
    rows = []
    for i, row in enumerate(a2d):
        for j, cell in enumerate(row):
            if i == 0:
                rows.append([])

            rows[j].append(cell)

    return rows


def findsign(array2d, verify):
    if not callable(verify):
        raise Exception(
            'signchecker not callable in signrow(array2d, signchecker)')

    ifrow = None

    for ir, row in enumerate(array2d):
        for ic, cell in enumerate(row):
            if not verify(cell):
                continue
            ifrow = ir
            break

    if ifrow is None:
        raise Exception('CAN NOT find sign row')

    signpos = []

    for ic, cell in enumerate(array2d[ifrow]):
        if not verify(cell):
            log(f'?? warning Column [{ctoa(ic)}] has NO sign. Ignore this column..')
            continue

        signpos.append(Coor(ifrow, ic))

    return signpos


def normalize(array2d, signpos):
    ifrow = signpos[0].r
    ifcol = signpos[0].c
    normalied = []
    index = 0

    for r in range(ifrow, len(array2d)):
        index += 1

        cells = array2d[r]
        maxcol = len(cells)

        first = None
        if ifcol < maxcol:
            first = cells[ifcol]

        # index 1 是字段行，index 2 可能是设置行，设置行有可能为空
        if index > 2:
            if first is None or first == '':
                log(f'-- warning {celltoa(r, ifcol)} is Empty. Ignore this line..')
                continue

            if first is str and '#' in first:
                continue

        newrow = []
        for coor in signpos:
            if coor.c >= maxcol:
                cell = None
            else:
                cell = trim(cells[coor.c])

            newrow.append((r, coor.c, cell))

        normalied.append(newrow)

    return normalied


def normalize_sheet(sheet: xlrd.sheet.Sheet, signverify, transpose):
    if not transpose:
        a2d = array2d(sheet)
    else:
        a2d = array2d_transpose(sheet)

    pos = findsign(a2d, signverify)
    n2d = normalize(a2d, pos)

    return n2d, a2d, pos[0]
