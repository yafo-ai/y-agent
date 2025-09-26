import { useVueFlow } from '@vue-flow/core'
import { ref, watch } from 'vue'

let id = 0

/**
 * @returns {string} - A unique id.
 */
function getId() {
  return 'n_' + Date.now()
}

/**
 * In a real world scenario you'd want to avoid creating refs in a global scope like this as they might not be cleaned up properly.
 * @type {{draggedType: Ref<string|null>, isDragOver: Ref<boolean>, isDragging: Ref<boolean>}}
 */
const state = {
  /**
   * The type of the node being dragged.
   */
  draggedType: ref(null),
  isDragOver: ref(false),
  isDragging: ref(false),
  nodes: ref([]),
}

export default function useDragAndDrop() {
  const { draggedType, isDragOver, isDragging, nodes } = state

  const { addNodes, screenToFlowCoordinate, onNodesInitialized, updateNode, ZoomTo } = useVueFlow()
  watch(isDragging, (dragging) => {
    document.body.style.userSelect = dragging ? 'none' : ''
  })

  function onDragStart(event, type, curnodes) {
    if (event.dataTransfer) {
      event.dataTransfer.setData('application/vueflow', type)
      event.dataTransfer.effectAllowed = 'move'
    }
    nodes.value = curnodes;
    draggedType.value = type
    isDragging.value = true

    document.addEventListener('drop', onDragEnd)
  }

  /**
   * Handles the drag over event.
   *
   * @param {DragEvent} event
   */
  function onDragOver(event) {
    event.preventDefault()

    if (draggedType.value) {
      isDragOver.value = true

      if (event.dataTransfer) {
        event.dataTransfer.dropEffect = 'move'
      }
    }
  }

  function onDragLeave() {
    isDragOver.value = false
  }

  function onDragEnd() {
    isDragging.value = false
    isDragOver.value = false
    draggedType.value = null
    document.removeEventListener('drop', onDragEnd)
  }

  /**
   * Handles the drop event.
   *
   * @param {DragEvent} event
   */
  function onDrop(event) {
    const position = screenToFlowCoordinate({
      x: event.clientX,
      y: event.clientY,
    })




    let curnode = initNode(draggedType.value, position);


    /**
     * Align node position after drop, so it's centered to the mouse
     *
     * We can hook into events even in a callback, and we can remove the event listener after it's been called.
     */
    const { off } = onNodesInitialized(() => {
      updateNode(curnode.id, (node) => ({
        position: { x: node.position.x - node.dimensions.width / 2, y: node.position.y - node.dimensions.height / 2 },
      }))

      off()
    })


    addNodes(curnode)



  }

  function getName(role, list) {

    let newName = role;
    let ci = -1;
    list.forEach((item, index) => {
      if (item.data.role === newName) {
        ci = index;
      }
    });
    if (ci !== -1) {
      // 重名 修改名称
      let nlist = newName.split('_');
      if (nlist.length > 1) {
        if (parseInt(nlist[nlist.length - 1]) == nlist[nlist.length - 1]) {
          // 如果是整数
          nlist[nlist.length - 1] = '_' + (parseInt(nlist[nlist.length - 1]) + 1);
        } else {
          // 如果不是整数
          nlist[nlist.length - 1] = nlist[nlist.length - 1] + '_1';
        }
      } else {
        nlist[nlist.length - 1] = nlist[nlist.length - 1] + '_1';
      }
      newName = nlist.join('');
      return getName(newName, list);
    } else {
      return newName;
    }

  };
 
  function initNode(item, position, nodeItem,nodelist) {
    if(nodelist && nodelist.length > 0){
      nodes.value = nodelist;
    }
    const nodeId = getId()
    let newNode = {
      type: 'card',
      data: item,
      position,
    }
    if(nodeItem){
      newNode = nodeItem;
    }
    newNode.id = nodeId;
    newNode.selected = false;
    newNode.data.id = Date.now();
    newNode.data.role = getName(newNode.data.role, nodes.value);
    if (item.type == 'loop') {
      console.log(newNode.data.height)
      newNode.style = { backgroundColor: 'none', width: newNode.data.width || '1000px', height: newNode.data.height || '850px' }
      // 如果是循环体  添加子节点
      setTimeout(() => {
        addNodes({
          id: getId(),
          type: 'card',
          data: {
            id:Date.now(),
            type: 'loop_start',
            width: '100px',
            isHideTitle: true,
            isopen: true,
            pid: newNode.data.id
          },
          position: {
            x: 40,
            y: 720
          },
          expandParent: true,
          parentNode: newNode.id
        })
      }, 70)
      
    }
    return newNode;

  }

  return {
    initNode,
    getId,
    getName,
    draggedType,
    isDragOver,
    isDragging,
    onDragStart,
    onDragLeave,
    onDragOver,
    onDrop,
  }
}
