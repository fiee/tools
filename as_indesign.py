#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AppleScript InDesign CS2 helpers
"""
__docformat__ = "restructuredtext"
import os, sys, shutil
from pprint import pprint
import unicodedata
from appscript import app, k
import mactypes

if 'epydoc' in sys.modules:
    # Don't run appscript for documentation
    InDesign = '<Application "Adobe InDesign CS2">'
    Finder   = '<Application "Finder">'
else:
    InDesign = app('Adobe InDesign CS2')
    InDesign.script_preferences.user_interaction_level = k.never_interact

    Finder = app('Finder')

def compose(path):
    """Normalize `path` (unicode) as composed unicode (see `unicodedata.normalize`)"""
    return unicodedata.normalize('NFD', os.path.abspath(path))

def ComposedAlias(path):
    """`mactypes.Alias` of unicode POSIX `path`. (existing files only!)"""
    return mactypes.Alias(compose(path))

def ComposedFile(path):
    """`mactypes.File` of unicode POSIX `path`. (nonexisting files also)"""
    return mactypes.File(compose(path))

def in_bounds(point, rect):
    """Is the point within the bounds? (Returns a boolean)

    :Parameters:
        point : tuple/list
            x, y
        rect : tuple/list
            top y, left x, bottom y, right x
    """
    return (point[0]>=rect[1] and point[0]<=rect[3] and point[1]>=rect[0] and point[1]<=rect[2])

def size_of(rect):
    """Return size of list|tuple `rect` (top, left, bottom, right) as tuple (width, height)"""
    return (rect[3] - rect[1], rect[2] - rect[0])

class InDesignException(Exception):
    """Nothing special"""
    pass

class InDesignStory(object):
    """Wrapper for one text flow of an InDesign document. TODO: implement"""

    def strip(self):
        """Delete empty lines at start and end"""
        while self._story.lines[1].get().strip()==u'':
            self._story.lines[1].delete()
        while self._story.lines[-1].get().strip()==u'':
            self._story.lines[-1].delete()
        return self._story


class InDesignPage(object):
    """Wrapper for one page of an InDesign document

    :Parameters:
        id, name, index, label, document_offset, applied_section, ... : (r/o misc)
            unchanged properties of the appscript object.
            label is writable.
        master : (int/str) 
            index or name of master page (template)
        name : (r/o string) 
            page name (number with prefix)
        number : (r/o int) 
            page number (index, document_offset)
        side : (str) 
            page orientation, one of 'right', 'left' or 'single'
        bounds : (r/o list) 
            page bounds [0, 0, height, width]
        margins : (r/o list) 
            page margins [top, left, bottom, right]
        inner_bounds : (r/o list) 
            type area bounds [top, left, bottom, right]
        columns : (r/o list) 
            positions of columns [[top, left, bottom, right], ...]
        column_gutter : (r/o float) 
            space between columns
        column_count : (r/o int) 
            number of columns
        column_width : (r/o float) 
            width of one column
        all_info : (r/o dict) 
            all of the above
    """

    #_properties = {}

    _side_mapping = {
        'left' : k.left_hand,
        'right' : k.right_hand,
        'single' : k.single_sided,
        k.left_hand : 'left',
        k.right_hand : 'right',
        k.single_sided : 'single'

    }

    def __init__(self, pageref, **kwargs):
        """
        :Parameters:
            pageref :
                page reference (from InDesign.document.pages[1])
            kwargs :
                keyword arguments, ignored at the moment
        """
        #self.__dict__['_pageref'] = pageref
        object.__setattr__(self, '_pageref', pageref)
        object.__setattr__(self, '_properties', dict())
        #self._properties = dict()
        #self._start()

    def _start(self):
        pass

    def reload(self):
        self._properties = {}
        self._start()

    def _get_number(self):
        if not 'number' in self._properties:
            self._properties['number'] = (self._pageref.index(), self._pageref.document_offset())
        return self._properties['number']
    
    def _set_number(self, value):
        raise AttributeError(u'Page number is read-only!')
    
    number = property(_get_number, _set_number, doc="""Page number (index, document_offset), read only""")
    
    def _get_name(self):        
        if not 'name' in self._properties:
            self._properties['name'] = self._pageref.name()
        return self._properties['name']
    
    def _set_name(self, value):
        raise AttributeError(u'Page name is read-only!')

    name = property(_get_name, _set_name, doc="""Page name (number with prefix), read only""")

    def _get_side(self):
        if not 'side' in self._properties:
            self._properties['side'] = self._side_mapping[self._pageref.side()]
        return self._properties['side']

    def _set_side(self, value):
        """set page orientation

        :value:
            (str/int) one of 'right', 'left', 'single'
            or k.right_hand, k.left_hand, k.single_sided
        """
        if value in (k.right_hand, k.left_hand, k.single_sided):
            self._pageref.side.set(value)
        elif value in ('right', 'left', 'single'):
            self._pageref.side.set(self._side_mapping[value])
        return self._side()

    side = property(_get_side, _set_side, doc="""page orientation, one of 'right', 'left' or 'single'""")

    def _get_bounds(self):
        if not 'bounds' in self._properties:
            self._properties['bounds'] = self._pageref.bounds()
        return self._properties['bounds']

    def _set_bounds(self):
        raise AttributeError(u'Bounds are read-only!')

    def _del_bounds(self):
        del self._properties['bounds']

    bounds = property(_get_bounds, _set_bounds, _del_bounds, doc = """page bounds [0, 0, height, width]""")

    def _get_margins(self):
        if not 'margins' in self._properties:
            pref = self._pageref.margin_preference
            if self.side == 'left':
                self._properties['margins'] = [ pref.top()[0], pref.right()[0], pref.bottom()[0], pref.left()[0] ]
            else:
                self._properties['margins'] = [ pref.top()[0], pref.left()[0], pref.bottom()[0], pref.right()[0] ]
        return self._properties['margins']

    def _set_margins(self, values):
        pref = self._pageref.margin_preference
        pref.top.set(values[0])
        pref.bottom.set(values[2])
        if self.side=='left':
            pref.right.set(values[1])
            pref.left.set(values[3])
        else:
            pref.left.set(values[1])
            pref.right.set(values[3])
        self.__delete__()
        return self.__get__()

    def _del_margins(self):
        del self._properties['margins']

    margins = property(_get_margins, _set_margins, _del_margins, doc = """page margins [top, left, bottom, right]""")

    def _get_inner_bounds(self):
        if not 'inner_bounds' in self._properties:
            b = self.bounds
            m = self.margins
            self._properties['inner_bounds'] = [ b[0]+m[0], b[1]+m[1], b[2]-m[2], b[3]-m[3] ]
        return self._properties['inner_bounds']

    def _set_inner_bounds(self, values):
        raise AttributeError(u'Cannot set inner_bounds, set margins instead!')

    def _del_inner_bounds(self):
        del self._properties['inner_bounds']

    inner_bounds = property(_get_inner_bounds, _set_inner_bounds, _del_inner_bounds, doc = """type area bounds [top, left, bottom, right]""")

    def _get_columns(self):
        if not 'columns' in self._properties:
            pref = self._pageref.margin_preferences
            cols = []
            inner = self.inner_bounds
            colnum = pref.column_count()
            gutter = pref.column_gutter()
            colwidth = (inner[3] - inner[1] - (gutter * (colnum-1))) / colnum
            rect = [inner[0], inner[1], inner[2], inner[1]+colwidth]
            self._properties['column_gutter'] = gutter
            self._properties['column_count'] = colnum
            self._properties['column_width'] = colwidth
            for n in range(pref.column_count()):
                cols.append(rect[:])
                rect[1] = rect[3] + gutter
                rect[3] += colwidth + gutter
            self._properties['columns'] = cols
        return self._properties['columns']

    def _set_columns(self, args):
        self.__delete__()
        pref = self._pageref.margin_preferences
        pref.column_count.set(args[0])
        pref.column_gutter.set(args[1])
        return self.__get__()

    def _del_columns(self):
        del self._properties['columns']
        del self._properties['column_gutter']
        del self._properties['column_count']
        del self._properties['column_width']

    columns = property(_get_columns, _set_columns, _del_columns,  \
        doc = """positions of columns
        get: [[top, left, bottom, right], ...]
        set: (count, gutter)""")

    @property
    def master():
        doc = """master spread (page template) as number, setting also as name possible"""

        def __get__(self):
            return self._pageref.applied_master.index()

        def __set__(self, value):
            master_list = self._pageref.master_spreads.base_name()
            if value in master_liste:
                self._pageref.applied_master.set(self._pageref.master_spreads[master_list.index(value)+1])
            else:
                self._pageref.applied_master.set(value)
            return self._master()

        def __delete__(self):
            self._pageref.applied_master.set(k.nothing)

    def __setattr__(self, name, value):
        self.__dict__['_properties'][name] = eval('self._pageref.%s.set("%s")' % (name, value))

    def __getattr__(self, name):
        #if hasattr(self, name): return getattr(self, name)
        if name in self.__dict__: return self.__dict__[name]
        if name in self._properties: return self._properties[name]
        #if name in self.__dict__['_pageref']: return self.__dict__['_pageref']['name']
        #pprint(self._properties)
        raise AttributeError("Unknown property, element or command: '%s'" % name)

    def all_info(self):
        self.bounds
        self.margins
        self.inner_bounds
        self.columns
        self.side
        #self.pagenumber
        #self.pagename
        return self._properties


class InDesignDocument(object):
    """
    wrapper for InDesign's document object
    
    The underlying AS document is accessable as .document
    """

    defaults = {
        'page' : 1,
        'addpage' : False,
        'showing_options' : False,
        'layer' : 1,
        'place_point' : [0,0],
        'rect' : [0,0,297,210],
        'add_page' : False,
    }

    def __init__(self, path, **kwargs):
        """
        path : path to InDesign file
        
        :Keywords:
            copy_from : path to template file (only used if path doesn't exist)
        """
        self.path = os.path.abspath(compose(path))
        if 'copy_from' in kwargs \
        and os.path.exists(os.path.abspath(compose(kwargs['copy_from']))) \
        and not os.path.exists(self.path):
            shutil.copy(os.path.abspath(compose(kwargs['copy_from'])), self.path) # Finder.copy?
        if os.path.exists(self.path):
            self.document = InDesign.open(mactypes.Alias(self.path))
        else:
            self.document = InDesign.make(new=k.document).save(to=mactypes.File(self.path)) # not chainable!
        self.alias = mactypes.Alias(self.path)
        pref = self.document.pages[1].margin_preference
        self.defaults['rect'] = [ pref.top()[0], pref.left()[0], pref.bottom()[0], pref.right()[0] ]

    def _get_masters(self):
        """
        get: list of documents master spreads (page templates)
        
        set: set master spread (page template) as name or number for all pages
        (set master for one page via `page.master`)"""
        return self.document.master_spreads.base_name()

    def _set_masters(self, value):
        """set the page template to all pages"""
        master_list = self.document.master_spreads.base_name()
        doc = self.document
        if value in master_list:
            #print "Set master to %s" % value
            doc.pages.applied_master.set(doc.master_spreads[master_list.index(value)+1])
        else:
            #print "Value %s is not in list of masters %s" % (value, master_list)
            try:
                doc.pages.applied_master.set(doc.master_spreads[int(value)])
            except:
                raise InDesignException(u'Master spread with name or number "%s" not found' % value)
            
    masters = property(_get_masters, _set_masters)

    def page(self, number, **kwargs):
        """return a `InDesignPage` object for page `number`

        :number:
            an integer index, 1-based (meaning the #th page in this document)
        
        :Keywords:
            add_page : bool
                add new page, if page `number` does not exist? Default: False
            
        """
        args = dict(self.defaults)
        args.update(**kwargs)
        if number > len(self.document.pages()) and args['add_page']:
            self.document.make(new=k.page, at=self.document.end)
        return InDesignPage(self.document.pages[number])
            

    def object_at(self, point, **kwargs):
        """
        Return the object at 'point' - None if not occupied.

        :point:
            (tuple/list of float x, y)

        :Keywords:
            page : (int) 
                page number. Default: 1
            layer : (int) 
                only objects on this layer (index). Default: 1
            type : (str/k) 
                only objects of this type (k.something)
            ignore_type : (list of str/k) 
                ignore objects of this type (k.something)
        """
        args = dict(self.defaults)
        args.update(**kwargs)
        page = self.document.pages[args['page']] # AS Pageref!
        #point = (point[0]+0.1, point[1]+0.1)
        point = list(point)
        rpoint = point[:] # needed for "within page bounds" check
        bounds = page.bounds()
        if bounds[1] > 0: # right page
            rpoint[0] += bounds[1]
        if not in_bounds(rpoint, bounds):
            raise InDesignException(u'Point %s is out of bounds %s!' % (point, bounds))
        for item in page.page_items():
            if in_bounds(point, item.geometric_bounds()):
                #pprint((args,item))
                ok=True
                if ('type' in kwargs and item.class_() != args['type']) \
                or ('layer' in kwargs and item.item_layer.index() != args['layer']) \
                or ('ignore_type' in kwargs and item.class_() not in kwargs['ignore_type']):
                    ok=False
                if ok: return item
        return None

    def place_item(self, path, **kwargs):
        """import a file and place it, return reference to it

        :Keywords:
            page : int
                page number. Default: 1
            layer : int
                index: Default: 1
            rect : list of float
                [top, left, bottom, right] Default: page bounds
            showing_options : bool
                show options dialogue? Default: False
            place_point : tuple x,y
                Default: (0, 0)
            add_page : bool
                add page if necessary?
        """
        args = dict(self.defaults)
        args.update(**kwargs)
        if args['page'] > len(self.document.pages()) and args['add_page']:
            self.document.make(new=k.page, at=self.document.end)
        item = self.document.place(ComposedAlias(path),
            on=self.document.pages[args['page']],
            showing_options=args['showing_options'],
            place_point=args['place_point'],
            destination_layer=self.document.layers[args['layer']]
            )
        id = os.path.splitext(os.path.basename(path))[0] # filename without extension
        item.label.set(id)
        if 'rect' in kwargs:
            try:
                frame = item.text_frames[1].get()
            except:
                frame = item
            frame.geometric_bounds.set(args['rect'])
        # Können wir die Seitenreferenz hier irgendwie aktualisieren?
        return item

    def place_text(self, path, **kwargs):
        """import a text file (e.g. InDesign tagged text) and place it

        optional keyword arguments: see `place_item`
        """
        args = dict(self.defaults)
        args.update(**kwargs)
        story = self.place_item(path, **args)
        # delete empty lines at start
        while story.lines[1].get().strip()==u'':
            story.lines[1].delete()
        frame = story.text_frames[1].get()
        page = self.page(args['page'])
        page.columns # init col values
        c = 0 # column width of text frame
        while frame.overflows() and c<3:
            c += 1
            # enlarge frame, fitting with columns
            args['rect'][3] += page.column_width + page.column_gutter
            frame.geometric_bounds.set(args['rect'])
            # TODO: check if on page? add page?
        story.label = path # ??
        return story

    def place_image(self, path, **kwargs):
        """import and place an image file

        optional keyword arguments: see also `place_item`

        :width OR height:
            (float) scale proportionally to this size
            if boath are given, it scales unpropotionally
        """
        image = self.place_item(path, **kwargs)
        if 'width' in kwargs or 'height' in kwargs:
            rect = image.geometric_bounds()
            size = size_of(rect)
            if 'width' in kwargs and 'height' in kwargs:
                rect[2] = rect[0] + kwargs['height']
                rect[3] = rect[1] + kwargs['width']
            elif 'width' in kwargs:
                rect[2] = rect[0] + size[1] * (size[0]/kwargs['width'])
                rect[3] = rect[1] + kwargs['width']
            else:
                rect[2] = rect[0] + kwargs['height']
                rect[3] = rect[1] + size[0] * (size[1]/kwargs['height'])
            image.geometric_bounds.set(rect)
        return image

    def next_free_pos(self, **kwargs):
        """calculate next column start without placed item

        optional keyword arguments (starting point):

        :page:
            (int) page number. Default: 1
        :addpage:
            (bool) add a page, if needed. Default: false
        :layer:
            (int) index: Default: 1
        :rect:
            (list of float) required space (NYI) [top, left, bottom, right] Default: page bounds
        :place_point:
            (tuple x,y) Starting point (e.g. y offset, NYI) Default: (0, 0)
        :xoffset:
            (int)
        :yoffset:
            (int)
        :ignore_type:
            (list of str/k) ignore objects of this type (k.something)
        :add_page:
            (bool) add page if necessary?
        
        returns:
            dict with keys 'page' (int) and 'rect' (list) OR None
        """
        args = dict(self.defaults)
        args.update(**kwargs)
        original_place_point = args['place_point']
        found = False
        while not found:
            page = self.page(args['page'], **args)
            bounds = page.bounds
            #print "Page %s (%s)" % (args['page'], page.side)
            for colrect in page.columns:
                rect = colrect
                if rect[1]>bounds[1]: # right side
                    rect[1] -= bounds[1]
                    rect[3] -= bounds[1]
                if 'place_point' in kwargs:
                    size = size_of(rect)
                    rect[0] = args['place_point'][1] # move y1
                    if rect[1] < args['place_point'][0]:
                        rect[1] = args['place_point'][0] # move x1
                        rect[3] = rect[1] + size[0] # calculate x2 from x1 and width
                
                #args['rect'] = rect
                #pprint(args)
                point = (rect[1], rect[0])
                #print "Is %s within %s? %s" % (point, rect, in_bounds(point, rect))
                obj = self.object_at(point, **args)
                if not obj:
                    args['rect'] = rect
                    return args
            args['page']+=1
            args['place_point'] = original_place_point


# document.[file_path|full_name]
# [document|page].margin_preferences.[bottom|left|right|top|column_count|column_gutter|columns_positions]
# document.baseline_frame_grid_option.[starting_offset_for_baseline_frame_grid|baseline_frame_grid_increment]
# document.document_preference.[]

if __name__ == '__main__':
    if len(sys.argv)<3:
        print "Hrabans InDesign toolbox demo"
        print "show info about InDesign document or place InDesign tagged text file"
        print "%s indd_path [txt_path]" % sys.argv[0]
        if len(sys.argv)==1: sys.exit(1)
    indd = InDesignDocument(unicode(sys.argv[1], 'utf-8'))
    print 'DEFAULTS'
    pprint(indd.defaults)
    
    print "NEXT FREE POSITION"
    free = indd.next_free_pos(layer=2, place_point=(12,76))
    pprint(free)
    
    print 'PAGE %d' % free['page']
    p1 = indd.page(free['page'])
    pprint(p1.all_info())
    print 'Name:\t%s' % p1.name
    print 'Number:\ti%d, o%d' % p1.number

    point = (free['rect'][1], free['rect'][0])
    obj = indd.object_at(point, page=free['page'], layer=2)
    print 'OBJECT at %d,%d:' % point
    if obj:
        #print obj
        print u'Class:\t%s' % (obj.class_())
        print u'Layer:\t%s (%s)' % (obj.item_layer.name(), obj.item_layer.index())
        print u'Size :\t(%1.1f, %1.1f)' % (size_of(obj.geometric_bounds()))
    else:
        print '(%s)' % obj
    if len(sys.argv) > 2:
        story = indd.place_text(unicode(sys.argv[2], 'utf-8'), page=free['page'], layer=2, rect=free['rect']) #[76, 12, 284, 65], place_point=[12,76])
        print story.label()
