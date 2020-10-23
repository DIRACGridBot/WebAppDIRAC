/**
 * This plugin can enable a cell to cell drag and drop operation within the same grid view.
 *
 * Note that the plugin must be added to the grid view, not to the grid panel. For example, using {@link Ext.panel.Table viewConfig}:
 *
 *      viewConfig: {
 *          plugins: {
 *              ptype: 'celldragdrop',
 *
 *              // Remove text from source cell and replace with value of emptyText.
 *              applyEmptyText: true,
 *
 *              //emptyText: Ext.String.htmlEncode('<<foo>>'),
 *
 *              // Will only allow drops of the same type.
 *              enforceType: true
 *          }
 *      }
 */
Ext.define("Ext.dirac.utils.PanelDragDrop", {
  extend: "Ext.AbstractPlugin",
  alias: "plugin.paneldragdrop",

  uses: ["Ext.dd.DragZone", "Ext.dd.DropZone"],

  /**
   * @cfg {Boolean} enforceType
   * Set to `true` to only allow drops of the same type.
   *
   * Defaults to `false`.
   */
  enforceType: false,

  /**
   * @cfg {Boolean} applyEmptyText
   * If `true`, then use the value of {@link #emptyText} to replace the drag record's value after a node drop.
   * Note that, if dropped on a cell of a different type, it will convert the default text according to its own conversion rules.
   *
   * Defaults to `false`.
   */
  applyEmptyText: false,

  /**
   * @cfg {Boolean} emptyText
   * If {@link #applyEmptyText} is `true`, then this value as the drag record's value after a node drop.
   *
   * Defaults to an empty string.
   */
  emptyText: "",

  /**
   * @cfg {Boolean} dropBackgroundColor
   * The default background color for when a drop is allowed.
   *
   * Defaults to green.
   */
  dropBackgroundColor: "green",

  /**
   * @cfg {Boolean} noDropBackgroundColor
   * The default background color for when a drop is not allowed.
   *
   * Defaults to red.
   */
  noDropBackgroundColor: "red",

  //<locale>
  /**
   * @cfg {String} dragText
   * The text to show while dragging.
   *
   * Two placeholders can be used in the text:
   *
   * - `{0}` The number of selected items.
   * - `{1}` 's' when more than 1 items (only useful for English).
   */
  //dragText: '{0} selected row{1}',
  //</locale>
  /**
   * @cfg {String} ddGroup
   * A named drag drop group to which this object belongs. If a group is specified, then both the DragZones and
   * DropZone used by this plugin will only interact with other drag drop objects in the same group.
   */
  ddGroup: "GridDD",

  /**
   * @cfg {Boolean} enableDrop
   * Set to `false` to disallow the View from accepting drop gestures.
   */
  enableDrop: true,

  /**
   * @cfg {Boolean} enableDrag
   * Set to `false` to disallow dragging items from the View.
   */
  enableDrag: true,

  /**
   * @cfg {Object/Boolean} containerScroll
   * True to register this container with the Scrollmanager for auto scrolling during drag operations.
   * A {@link Ext.dd.ScrollManager} configuration may also be passed.
   */
  containerScroll: false,

  init: function(view) {
    var me = this;

    view.on("render", me.onViewRender, me, {
      single: true
    });
  },

  destroy: function() {
    var me = this;

    Ext.destroy(me.dragZone, me.dropZone);
  },

  enable: function() {
    var me = this;

    if (me.dragZone) {
      me.dragZone.unlock();
    }
    if (me.dropZone) {
      me.dropZone.unlock();
    }
    me.callParent();
  },

  disable: function() {
    var me = this;

    if (me.dragZone) {
      me.dragZone.lock();
    }
    if (me.dropZone) {
      me.dropZone.lock();
    }
    me.callParent();
  },

  onViewRender: function(view) {
    var me = this,
      scrollEl;

    if (me.enableDrag) {
      if (me.containerScroll) {
        scrollEl = view.getEl();
      }

      me.dragZone = new Ext.dd.DragZone(view.getEl(), {
        view: view,
        ddGroup: me.dragGroup || me.ddGroup,
        dragText: me.dragText,
        containerScroll: me.containerScroll,
        scrollEl: scrollEl,
        getDragData: function(e) {
          var view = this.view,
            item = e.getTarget().id,
            record = view.getComponent(item);
          if (item) {
            return {
              event: new Ext.EventObjectImpl(e),
              item: e.target,
              record: record
            };
          }
        },

        onInitDrag: function(x, y) {
          var self = this,
            data = self.dragData,
            view = self.view,
            //selectionModel = view.getSelectionModel(),
            record = data.record,
            el = data.ddel;

          // Update the selection to match what would have been selected if the user had
          // done a full click on the target node rather than starting a drag from it.
          //        if (!selectionModel.isSelected(record)) {
          //        selectionModel.select(record, true);
          //        }

          //        self.ddel.update(el.textContent || el.innerText);
          //        self.proxy.update(self.ddel.dom);
          self.onStartDrag(x, y);
          return true;
        }
      });
    }

    if (me.enableDrop) {
      me.dropZone = new Ext.dd.DropZone(view.el, {
        view: view,
        ddGroup: me.dropGroup || me.ddGroup,
        containerScroll: true,

        getTargetFromEvent: function(e) {
          var me = this,
            v = me.view,
            image = e.getTarget(),
            imageid,
            imageobj;

          // Ascertain whether the mousemove is within a grid cell.
          if (image) {
            imageid = image.id;
            if (imageid) {
              imageobj = view.getComponent(imageid);
              return {
                node: imageobj,
                record: imageobj
              };
            }
          }
        },

        // On Node enter, see if it is valid for us to drop the field on that type of column.
        onNodeEnter: function(target, dd, e, dragData) {
          var me = this;
          if (target.record != null) {
            //only allow to drop element, if the target an image. What about copy from other window?
            var destType = target.record.id,
              sourceType = dragData.record.id;
            //destType = target.record.fields.get(target.columnName).type.type.toUpperCase(),
            //sourceType = dragData.record.fields.get(dragData.columnName).type.type.toUpperCase();

            delete me.dropOK;

            // Return if no target node or if over the same cell as the source of the drag.
            if (!target || target.node.id === dragData.item.id) {
              // dragData.record.el.frame("#ff0000",1);
              return;
            }

            me.dropOK = true;
          } else {
            me.dropOK = false;
          }
        },

        // Return the class name to add to the drag proxy. This provides a visual indication
        // of drop allowed or not allowed.
        onNodeOver: function(target, dd, e, dragData) {
          return this.dropOK ? this.dropAllowed : this.dropNotAllowed;
        },

        // Highlight the target node.
        /*onNodeOut: function (target, dd, e, dragData) {
          if (target.node.id === dragData.item.id) {
            dragData.record.el.frame("#FFFFFF",1);
          }else{
            target.node.el.frame("#397D02",1);
          }
        },*/

        // Process the drop event if we have previously ascertained that a drop is OK.
        onNodeDrop: function(target, dd, e, dragData) {
          if (this.dropOK) {
            //target.node.el.frame("#397D02",1);
            var index = view.items.indexOf(target.record);
            view.insert(index, dragData.record);
            return true;
          }
        },

        onCellDrop: Ext.emptyFn
      });
    }
  }
});
