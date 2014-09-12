import xlrd

from common import models


def load(filename, version, volume, rootname):
    vol = models.BookVolume.objects.get(name=volume, version__name=version)
    wb = xlrd.open_workbook(filename)
    sheet = wb.sheets()[0]
    root = models.CourseTree.objects.create(volume=vol, name=rootname, level=0)
    parent_stack = [root]
    level = sheet.ncols
    for i in xrange(1, sheet.nrows):
        fields = sheet.row_values(i)
        for j in xrange(0, level):
            if fields[j]:
                if j == 0:
                    parent_stack = [root]
                node = models.CourseTree.objects.create(
                    volume=vol, name=fields[j], level=j + 1,
                    parent=parent_stack[-1]
                )
                parent_stack.append(node)
            else:
                parent_stack.pop()


def export(course_id, class_id):
    qs = models.CourseTree.objects.filter(volume__course=course_id, volume__classes=class_id)
    tree = {}
    parent = {}
    for ct in qs:
        children = []
        parent[ct.id] = children
        if ct.parent_id:
            pchildren = parent.setdefault(ct.parent_id, [])
            pchildren.append(dict(id=ct.id, name=ct.name, children=children))
        else:
            tree = dict(id=ct.id, name=ct.name, children=children)
    return tree
    