# -*- coding: utf-8 -*-

import numpy as np
import json,os
from PIL import Image

def get_json(cd):
    with open(cd, encoding='utf-8') as f:
        line = f.read()
        json_file = json.loads(line)
        f.close()

    return json_file['activity']['root']

def get_width(bounds):
    assert bounds[2]-bounds[0] > 0
    return bounds[2]-bounds[0]

def get_height(bounds):
    assert bounds[3]-bounds[1] > 0
    return bounds[3]-bounds[1]

def get_bound_asname(bound):
    _b = ''
    for b in bound:
        _b += str(b)+','
    return _b

def get_layerNumber(c):
    return int(c.split('_')[-1].split('-')[0])

def get_className(c):
    return c.split('.')[-1]

def get_father(c):
    d = c.split('_')[-1]
    sr = c.find(d)
    return c[:sr-1]

def judge_loc_height(bounds):
    y1 = bounds[0][1]
    y2 = bounds[0][3]
    height = get_height(bounds[0])
    for b in bounds[1:]:
        if b[1] == y1 and b[3] == y2 and get_height(b) == height:
            continue
        else:
            return False
    return True

def get_subNodes_ofC1(c,Dd): # find node only belongs to c in Dd
    Dd_ids = [d[0] for d in Dd]
    c_children = []
    for d in Dd_ids:
        if c in d:
            if d not in c_children:
                c_children.append(d) # all children of c
    # find node only belongs to c
    others_subNodes = []
    for d in c_children: #if there are other fathers of d
        c_children1 = c_children.copy()
        c_children1.remove(d)
        for f in c_children1: # traversal in all Dd but d
            if f in d:
                if d not in others_subNodes:
                    others_subNodes.append(d)
    c_children = [c for c in c_children if c not in others_subNodes]
    return c_children

'''put all tree_info of one GUI in a List'''
def get_DOM(list_Dom, father, layer_num, last_layer='0-0'):
    if('children' in father):
        i = 0
        next_layer_num = layer_num + 1
        for child in father['children']:
            if child is None:
                continue
            c_layer = str(layer_num)+'-'+str(i)
            if('resource-id' in child and child is not None):
                _id = child['resource-id']
            else:
                _id = ''
            if('children' in child):
                _children_num = len(child['children'])
            else:
                _children_num = 0
            link = last_layer +'_'+c_layer

            if child['visible-to-user']==True:
                list_Dom.append([link,child['class'],child['bounds'],_children_num,_id])
            i += 1
            get_DOM(list_Dom, child, next_layer_num, link)

def DeleteOverSize(_list):
    list_ddsf_leaf4 = []
    for c in _list:
        w = get_width(c[2]); h = get_height(c[2])
        if w/h >= 30 or h/w >= 50:
            print('illegal aspect ratio')
            continue
        elif h >= 1280 or h <5:
            print('illegal height')
            continue
        elif h <= 150 and w <= 800:
            print('too small piece')
            continue
        elif w <= 1000:
            print('not wide enough')
            continue
        else:
            list_ddsf_leaf4.append(c)
    return list_ddsf_leaf4

def DeleteOverlap(_list):
    blank_num = 0
    blank_ls = []
    blank_lsd = {}
    last_loc = 0
    m = 0
    out = _list.copy()
    list_wb = []
    if len(_list)>0:
        list_wb.append(_list[0][0])
    list_wb_del = []
    # record info of blank???order by(1)top left coordinate,(2)height
    for l in _list:
        loc1 = int(l[2][1])  # Top coordinates
        loc2 = int(l[2][-1]) # Bottom coordinates
        print('m: ', m, 'l: ', l[0])
        print('m: ', m, 'top loc1: ', loc1, 'bottom loc2: ', loc2)
        if m > 0:
            blank_num += 1
            print('loc: ', last_loc, loc1)
            bk = loc1 - last_loc
            print('blank: ', bk)
            if bk < 0:
                bk = -1
                out.remove(l)
                list_wb_del.append(l[0])
                if loc2>last_loc: # 2.
                    last_loc = loc2
            else:
                if bk != 0:
                    list_wb.append('bk_'+str(bk))
                last_loc = loc2
            if bk not in blank_ls:
                blank_ls.append(bk)
                blank_lsd[bk] = 1
            else:
                blank_lsd[bk] += 1
            list_wb.append(l[0])
        else:
            last_loc = loc2
        m += 1
    return out, list_wb, list_wb_del

def get_component_byjson(json_file):

    '''read json file to get tree info'''
    a0 = get_json(json_file)
    list_Dom = []
    get_DOM(list_Dom,a0,1)

    '''del subtrees(sts) with duplicate bounds and leave one'''
    same_bounds_dict = {}
    same_bounds_list = []
    for c in list_Dom:
        if c[2] not in same_bounds_list:# new bounds
            _bounds = c[2]
            same_bounds_list.append(_bounds)
            same_bounds_dict[get_bound_asname(_bounds)] = [c[0]]
        else:                           # old bounds
            same_bounds_dict[get_bound_asname(c[2])].append(c[0])

    same_bounds_dict1 = same_bounds_dict.copy()
    for (k,v) in same_bounds_dict.items():
        if len(v) == 1:
            same_bounds_dict1.pop(k,v)

    list_for_del = []
    for (k,v) in same_bounds_dict1.items():
        last_id_len = np.max([len(vs) for vs in v])
        last_ids = [c for c in v if len(c)==last_id_len]
        for c in v: # leave the last samebounds
            if c !=last_ids[-1]:
                list_for_del.append(c)

    # delete
    list_Dom_del_st = [c for c in list_Dom if c[0] not in list_for_del]

    list_Dom_del_st_fit = [c for c in list_Dom_del_st if c[2][2]>c[2][0] and c[2][3]>c[2][1] and c[0]!='0-0_1-0']
    list_ddsf_leaf = [c for c in list_Dom_del_st_fit if c[3]==0]
    list_ddsf_node = [c for c in list_Dom_del_st_fit if c[3]!=0]

    #------------------------------------------------------------------------------------#
    # Find the node with the same father
    # (1)by bounds (2) remove the covered ones, 
    # (3)remove all subtrees in the same row with the same length and height

    node_fs_l = [] # Constructing the L, D of the fathers node
    node_fs_d = {} # key:father, value:children(nodes in list_ddsf_node)
    for c in list_ddsf_node:
        if get_father(c[0]) not in node_fs_l:
            node_fs_l.append(get_father(c[0]))
            node_fs_d[get_father(c[0])] = [c[0]]
        else:
            node_fs_d[get_father(c[0])].append(c[0])

    c_for_del = [] # Nodes whose width exceeds the limit need to be pruned (delete all their children subtrees)
    width_r = 0.95
    w_limit = 1440 * width_r
    for (k,v) in node_fs_d.items():
        if len(v)>2:
            for c in v:
                if get_width([i[2] for i in list_ddsf_node if i[0]==c][0]) >= w_limit:
                    c_for_del.append(c)

    '''Delete children st beyond limited width'''
    list_ddsfcutfc_cb = list_ddsf_node.copy()
    for c in list_ddsf_node:
        for d in c_for_del:
            if d in c[0] and d!=c[0]:
                if c in list_ddsfcutfc_cb:
                    list_ddsfcutfc_cb.remove(c)
#    print('Delete',del_node_num,'nodes from list_ddsf_node\n') # (1)Finished
    list_ddsfcutfccb_ch = list_ddsfcutfc_cb.copy()

    #------------------------------------------------------------------------------------#
    '''find sts with same loc_height'''
    node1_fs_l = []
    node1_fs_d = {}
    for c in list_ddsfcutfccb_ch:
        if get_father(c[0]) not in node1_fs_l:
            node1_fs_l.append(get_father(c[0]))
            node1_fs_d[get_father(c[0])] = [(c[0],c[2])]
        else:
            node1_fs_d[get_father(c[0])].append((c[0],c[2]))

    list_for_del_slh = []
    # On the same line, y1 is the same, y2 is the same, and so is height
    for (k,v) in node1_fs_d.items():
        if len(v)>2:
            _bounds = [c[1] for c in v]
            # For nodes with more than two brothers, judge whether they are in the same line and 
            # of the same height. If yes, cut them off (their children should also be cut off)
            if judge_loc_height(_bounds)==True:
                for c in v:
                    if c[0] not in list_for_del_slh:
                        list_for_del_slh.append(c[0])
                    for d in list_ddsfcutfccb_ch:
                        if c[0] in d[0] and c[0] != d[0]:
                            if d[0] not in list_for_del_slh:
                                list_for_del_slh.append(d[0])

    list_ddsfcutfccbch_cslh=[c for c in list_ddsfcutfccb_ch if c[0] not in list_for_del_slh] # (3)Finished

    #cslh Delete c of the same height and record the blanks
    '''del sts with the same height in one line'''
    l_delete = []
    for c in list_ddsfcutfccbch_cslh:
        c_height = get_height(c[2])
        l_e_c = list_ddsfcutfccbch_cslh.copy()
        l_e_c.remove(c)
        if l_e_c != []:
            c_children = get_subNodes_ofC1(c[0],l_e_c)
            print('c_children',c_children)
            for d in c_children:
                d_bound = [f[2] for f in list_ddsfcutfccbch_cslh if f[0]==d]
                d_height = get_height(d_bound[0])
                print('d:',d,',height:',d_height)
                if c_height == d_height:
                    if d not in l_delete:
                        l_delete.append(d)
                        for d1 in list_ddsfcutfccb_ch:
                            if d in d1[0] and d != d1[0]:
                                print('delete d',d,'children',d1[0])
                                if d1[0] not in l_delete:
                                    l_delete.append(d1[0])
        else:
            print('c_children is []')
    list_ddsfcutfccbch_cslh1 = [c for c in list_ddsfcutfccbch_cslh if c[0] not in l_delete]

    print('\ndelete subtree not fit:')
    list_ddsfcutfccbch_cslh_cutlwR2 = DeleteOverSize(list_ddsfcutfccbch_cslh1) #(4) Finished

    #------------------------------------------------------------------------------------#
    '''sort subtrees by coordinates and delete overlap'''
    list_ddsfcutfccbch_cslh_cutlwR2 = sorted(list_ddsfcutfccbch_cslh_cutlwR2,key=lambda x: (int(x[2][1]), 1/get_height(x[2])))
    list_ddsfcutfccbch_cslh_cutlwR3,_,_ = DeleteOverlap(list_ddsfcutfccbch_cslh_cutlwR2)

    #------------------------------------------------------------------------------------#
    '''add leafnodes(fit) to subtrees'''
    list_ddsf_leaf0 = []
    for c in list_ddsf_leaf:
        for f in list_ddsfcutfccbch_cslh_cutlwR3:
            if f[0] in c[0]:
                if c not in list_ddsf_leaf0:
                    list_ddsf_leaf0.append(c)

    list_ddsf_leaf2 = [c for c in list_ddsf_leaf if c[0] not in [d[0] for d in list_ddsf_leaf0]]

    list_ddsf_leaf3 = [c for c in list_ddsf_leaf2 if not (c[0] in ['0-0_1-1', '0-0_1-2'] and c in list_ddsf_leaf2)]

    list_ddsf_leaf4 = DeleteOverSize(list_ddsf_leaf3)

    '''sort subtrees by coordinates and delete overlap'''
    list_ddsfcutfccbch_cslh_cutlwR4 = list_ddsfcutfccbch_cslh_cutlwR3+list_ddsf_leaf4
    list_ddsfcutfccbch_cslh_cutlwR4 = sorted(list_ddsfcutfccbch_cslh_cutlwR4,key=lambda x: (int(x[2][1]), 1/get_height(x[2])))

    # The second time with leaf_node
    print('\nsecond sort and sel blank')
    list_ddsfcutfccbch_cslh_cutlwR5,list_ddsfcutfccbch_cslh_cutlwR2_wb,list_ddsfcutfccbch_cslh_cutlwR2_wb_del = DeleteOverlap(list_ddsfcutfccbch_cslh_cutlwR4)
    list_ddsfcutfccbch_cslh_cutlwR2_wb1 = [c for c in list_ddsfcutfccbch_cslh_cutlwR2_wb if c not in list_ddsfcutfccbch_cslh_cutlwR2_wb_del]
    list_ddsfcutfccbch_cslh_cutlwR3 = list_ddsfcutfccbch_cslh_cutlwR5
    #------------------------------------------------------------------------------------#
    ''''del st in same father with partially covered'''
    c_for_del = [c for c in c_for_del if c in [d[0] for d in list_ddsfcutfccbch_cslh_cutlwR3]]
    c_for_del_heights = [(c,get_height([i[2] for i in list_ddsfcutfccbch_cslh_cutlwR3 if i[0]==c][0])) for c in c_for_del]
    node_heght_l = []
    node_heght_d = {}
    for c in c_for_del_heights:
        if c[1] not in node_heght_l:
            node_heght_l.append(c[1])
            node_heght_d[c[1]] = [c[0]]
        else:
            node_heght_d[c[1]].append(c[0])
    del_dif_height = []
    for (k,v) in node_heght_d.items():
        if len(v) == 1:
            del_dif_height.append(v[0])
            for d in list_ddsfcutfccbch_cslh_cutlwR3:
                if v[0] in d[0] and v[0] != d[0]:
                    del_dif_height.append(d[0]) # del their children

    list_ddsfcutfccb_ch1 = [c for c in list_ddsfcutfccbch_cslh_cutlwR3 if c[0] not in del_dif_height] # (2)Finished

    #------------------------------------------------------------------------------------#
    '''save_st_with_blank file'''
    list_ddsfcutfccbch_cslh_cutlwR3_wb = list_ddsfcutfccbch_cslh_cutlwR2_wb1.copy()
    for c in list_ddsfcutfccbch_cslh_cutlwR2_wb1:
        if c.split('_')[0] != 'bk':
            if c not in [d[0] for d in list_ddsfcutfccb_ch1]:
                list_ddsfcutfccbch_cslh_cutlwR3_wb.remove(c)

    #------------------------------------------------------------------------------------#
    '''delete st without enough area'''
    S0 = 1440 * 2560 / 2 # half area of GUI
    S = 0
    for x in list_ddsfcutfccb_ch1:
        S += get_width(x[2]) * get_height(x[2])
    if S <= S0:
        print('square unsatisfy')
        ##list_ddsfcutfccb_ch1 = []
    else:
        print('square satisfy')

    return list_ddsfcutfccb_ch1,list_ddsf_leaf0,list_ddsfcutfccbch_cslh_cutlwR3_wb

def get_resized_bounds(block,rate = 8/3):
    resized_block = []
    for i in range(len(block)):
        resized_block.append(int(block[i])/ rate)
    return resized_block

def compress_image(srcPath, dstPath, width, height):
    for filename in os.listdir(srcPath):
        print('filename:',filename)
        if not os.path.exists(dstPath):
                os.makedirs(dstPath)

        srcFile=os.path.join(srcPath,filename)
        dstFile=os.path.join(dstPath,filename)
        print('srcFile:',srcFile)
        print('dstFile:',dstFile)

        if os.path.isfile(srcFile):
            if os.path.splitext(srcFile)[1] == '.jpg' or os.path.splitext(srcFile)[1] == '.bmp' or os.path.splitext(srcFile)[1] == '.png':
                sImg = Image.open(srcFile)
                dImg = sImg.resize((width,height),Image.ANTIALIAS)
                dImg.save(dstFile)
                print(dstFile+" compressed succeeded")

        if os.path.isdir(srcFile):
            compress_image(srcFile, dstFile, width, height)