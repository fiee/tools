#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
InDesign helpers
"""
import os, sys, shutil
from pprint import pprint
import unicodedata
from appscript import app, k
import mactypes

InDesign = app('Adobe InDesign CS2')
InDesign.script_preferences.user_interaction_level = k.never_interact

Finder = app('Finder')

def compose(path):
    """Normalize ``path`` (unicode) as composed unicode (see ``unicodedata.normalize``)"""
    return unicodedata.normalize('NFD', os.path.abspath(path))

def ComposedAlias(path):
    """``mactypes.Alias`` of unicode POSIX ``path``. (existing files only!)"""
    return mactypes.Alias(compose(path))

def ComposedFile(path):
    """``mactypes.File`` of unicode POSIX ``path``. (nonexisting files also)"""
    return mactypes.File(compose(path))

def in_bounds(point, rect):
    """Is the point within the bounds? (Returns a boolean)
    
    :point:
        (tuple/list) x, y
    :rect:
        (tuple/list) top y, left x, bottom y, right x
    """
    return (point[0]>=rect[1] and point[0]<=rect[3] and point[1]>=rect[0] and point[1]<=rect[2])

def size_of(rect):
    """Return size of liste|tuple ``rect`` (top, left, bottom, right) as tuple (width, height)"""
    return (rect[3] - rect[1], rect[2] - rect[0])

class InDesignException(Exception):
    """Nothing special"""
    pass

class InDesignStory:
    """Wrapper for one text flow of an InDesign document. NYI"""
    pass

class InDesignPage:
    """Wrapper for one page of an InDesign document
    
    Properties:
    
    :id, name, index, label, document_offset, applied_section, ...:
        (r/o misc) unchanged properties of the appscript object.
        label is writable.
    :master:
        (int/str) index or name of master page (template)
    :side:
        (str) page orientation, one of 'right', 'left' or 'single'
    :bounds:
        (r/o list) page bounds [0, 0, height, width]
    :margins:
        (r/o list) page margins [top, left, bottom, right]
    :inner_bounds:
        (r/o list) type area bounds [top, left, bottom, right]
    :columns:
        (r/o list) positions of columns [[top, left, bottom, right], ...]
    :column_gutter:
        (r/o float) space between columns
    :column_count:
        (r/o int) number of columns
    :column_width:
        (r/o float) width of one column
    :all_info:
        (r/o dict) all of the above
    """

    _properties = {}
    
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
        :pageref:
            page reference (from InDesign.document.pages[1])
        :kwargs:
            keyword arguments, ignored at the moment
        """
        self._pageref = pageref
        self._start()

    def _start(self):
        pass

    def reload(self):
        self._properties = {}
        self._start()
        
    def __getattr__(self, name):
        if self.hasattr('_'+name):
            return self.getattr('_'+name)()
        if not name in self._properties:
            if name.startswith('column_'): 
                self._columns()
            else:
                self._properties[name] = eval('self._pageref.%s()' % name)
        return self._properties[name]
        
    def __setattr__(self, name, value):
        self._properties[name] = eval('self._pageref.%s.set("%s")' % (name, value))
    
    master = property(_master, _set_master, None, 'master page / template')
    side = property(_side, _set_side, None, 'page orientation, one of "right", "left" or "single"')
    
    @property
    def all_info(self):
        self.bounds()
        self.margins()
        self.inner_bounds()
        self.columns()
        self.side()
        return self._properties
    
    def _side(self):
        """page orientation, one of 'right', 'left' or 'single'"""
        if not 'side' in self._properties:
            self._properties['side'] = self._side_mapping[self._pageref.side()]
        return self._properties['side']

    def _set_side(self, value):
        """set page orientation
        
        :value:
            (str/int) one of 'right', 'left', 'single'
            or k.right_hand, k.left_hand, k.single_sided
        """
        if value in (k.right_hand, k.left_hand, k.single_sided)
            self._pageref.side.set(value)
        elif value in ('right', 'left', 'single'):
            self._pageref.side.set(self._side_mapping[value])
        return self._side()

    def _bounds(self):
        """page bounds [0, 0, height, width]"""
        if not 'bounds' in self._properties:
            self._properties['bounds'] = self._pageref.bounds()
        return self._properties['bounds']
    
    def _margins(self):
        """page margins [top, left, bottom, right]"""
        if not 'margins' in self._properties:
            pref = self._pageref.margin_preference
            self._properties['margins'] = [ pref.top()[0], pref.left()[0], pref.bottom()[0], pref.right()[0] ]
        return self._properties['margins']
        
    def _inner_bounds(self):
        """type area bounds [top, left, bottom, right]"""
        if not 'inner_bounds' in self._properties:
            b = self.bounds
            m = self.margins
            self._properties['inner_bounds'] = [ b[0]+m[0], b[1]+m[1], b[2]-m[2], b[3]-m[3] ]
        return self._properties['inner_bounds']

    def _columns(self):
        """positions of columns [[top, left, bottom, right], ...]"""
        if not 'columns' in self._properties:
            pref = self._pageref.margin_preferences
            cols = []
            inner = self.inner_bounds
            colnum = pref.column_count
            gutter = pref.column_gutter
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

    def _master(self):
        return self._pageref.applied_master.index()

    def _set_master(self, value):
        master_list = self._pageref.master_spreads.base_name()
        if value in master_liste:
            self._pageref.applied_master.set(self._pageref.master_spreads[master_list.index(value)+1])
        else:
            self._pageref.applied_master.set(value)
        return self._master()



class InDesignDocument:
    """
    wrapper for InDesign's document object
    """

    defaults = {
        'page' : 1,
        'showing_options' : False,
        'layer' : 1,
        'place_point' : [0,0],
        'rect' : [0,0,297,210]
    }

    def __init__(self, path, **kwargs):
        """
        kwargs:
        copy_from : path to template file
        """
        self.path = os.path.abspath(compose(path))
        if 'copy_from' in kwargs and os.path.exists(os.path.abspath(compose(kwargs['copy_from']))):
            shutil.copy(os.path.abspath(compose(kwargs['copy_from'])), self.path) # Finder.copy?
        if os.path.exists(self.path):
            self.document = InDesign.open(mactypes.Alias(self.path))
        else:
            self.document = InDesign.make(new=k.document).save(to=mactypes.File(self.path)) # not chainable!
        self.alias = mactypes.Alias(self.path)
        pref = self.document.pages[1].margin_preference
        self.defaults['rect'] = [ pref.top()[0], pref.left()[0], pref.bottom()[0], pref.right()[0] ]

    def master_spreads(self):
        return self.document.master_spreads()

    def page(self, number):
        """return a _`InDesignPage` object for page ``number``
        
        :number:
            an integer index, 1-based
        """
        return InDesignPage(self.document.pages[number])

    def set_master_spread(self, name):
        """set the page template to all pages"""
        # TODO: for single page(s)
        master_list = self.document.master_spreads.base_name()
        if name in master_list:
            self.document.pages.applied_master.set(doc.master_spreads[master_list.index(name)+1])
        else:
            raise InDesignException(u'Master spread with name "%s" not found' % name)

    def object_at(self, point, **kwargs):
        """
        Return the object at 'point' - None if not occupied.
        
        :point:
            (tuple/list of float x, y)
        
        optional keyword arguments:
        
        :page:
            (int) page number. Default: 1
        :layer:
            (int) only objects on this layer (index). Default: 1
        :type:
            (str/k) only objects of this type (k.something)
        :ignore_type:
            (list of str/k) ignore objects of this type (k.something)
        """
        args = dict(self.defaults)
        args.update(**kwargs)
        page = self.document.pages[args['page']]
        if not in_bounds(point, page.bounds()):
            raise InDesignException(u'Point (%d, %d) is out of bounds %s!' % (point[0], point[1], page.bounds()))
        for item in page.page_items():
            if in_bounds(point, item.geometric_bounds()):
                ok=True
                if ('type' in kwargs and item.class_() != args['type']) \
                or ('layer' in kwargs and item.item_layer.id() != args['layer']) \
                or ('ignore_type' in kwargs and item.class_() not in kwargs['ignore_type']):
                    ok=False
                if ok: return item
        return None

    def place_item(self, path, **kwargs):
        """import a file and place it, return reference to it
        
        optional keyword arguments:
        
        :page:
            (int) page number. Default: 1
        :layer:
            (int) index: Default: 1
        :rect:
            (list of float) [top, left, bottom, right] Default: page bounds
        :showing_options:
            (bool) show options dialogue? Default: False
        :place_point:
            (tuple x,y) Default: (0, 0)
        """
        args = dict(self.defaults)
        args.update(**kwargs)
        item = self.document.place(ComposedAlias(path), 
            on=self.document.pages[args['page']], 
            showing_options=args['showing_options'], 
            place_point=args['place_point'], 
            destination_layer=self.document.layers[args['layer']]
            )
        if 'rect' in kwargs:
            item.geometric_bounds.set(args['rect'])
        return item

    def place_text(self, path, **kwargs):
        """import a text file (e.g. InDesign tagged text) and place it
        
        optional keyword arguments: see place_item
        """
        story = self.place_item(path, **kwargs)
        # delete empty lines at start
        while story.lines[1]=='':
            story.lines[1].delete()
        frame = story.text_frames[1].get()
        if frame.overflows():
            pass
            # TODO: enlarge frame, fitting with columns
        return story

    def place_image(self, path, **kwargs):
        """import and place an image file
        
        optional keyword arguments: see also place_item
        
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
        :layer:
            (int) index: Default: 1
        :rect:
            (list of float) required space (NYI) [top, left, bottom, right] Default: page bounds
        :place_point:
            (tuple x,y) Default: (0, 0)
        :ignore_type:
            (list of str/k) ignore objects of this type (k.something)
        """
        args = dict(self.defaults)
        args.update(**kwargs)
        found = False
        while not found:
            page = self.page(args['page'])
            for colrect in page.columns:
                obj = self.object_at((colrect[1], colrect[y]), **args):
                    return colrect
            args['page']+=1
        
        # TODO
        

# document.[fiel_path|full_name]
# [document|page].margin_preferences.[bottom|left|right|top|column_count|column_gutter|columns_positions]
# document.baseline_frame_grid_option.[starting_offset_for_baseline_frame_grid|baseline_frame_grid_increment]
# document.document_preference.[]

if __name__ == '__main__':
    indd = InDesignDocument(unicode(sys.argv[1], 'utf-8'))
    obj = indd.object_at((5.1,10.1), page=1)
    pprint(indd.defaults)
    p1 = InDesignPage(indd.document.pages.first())
    pprint(p1.all_info())
    if obj:
        #print obj
        print u'Class:\t%s' % (obj.class_())
        print u'Layer:\t%s (%s)' % (obj.item_layer.name(), obj.item_layer.index())
        print u'Size :\t(%1.1f, %1.1f)' % (size_of(obj.geometric_bounds()))
        while obj.lines[1]=='':
            obj.lines[1].delete()
    else:
        print 'No object at this place!\n%s' % obj
    if len(sys.argv) > 2:
        indd.place_text(unicode(sys.argv[2], 'utf-8'))
        