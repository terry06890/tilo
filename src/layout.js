export {staticSqrLayout, staticRectLayout, sweepToSideLayout};

const TILE_SPACING = 5;
const HEADER_SZ = 20;

const staticSqrLayout = { //lays out nodes as squares in a rectangle, with spacing
	genLayout(node, x, y, w, h, hideHeader){
		//get number-of-columns with lowest leftover empty space
		let headerSz = (hideHeader ? 0 : HEADER_SZ);
		let availW = w - TILE_SPACING, availH = h - headerSz - TILE_SPACING;
		let numChildren = node.children.length, ar = availW/availH;
		let lowestEmp = Number.POSITIVE_INFINITY, numCols, numRows, tileSize;
		for (let nc = 1; nc <= numChildren; nc++){
			let nr = Math.ceil(numChildren/nc);
			let ar2 = nc/nr;
			let frac = ar > ar2 ? ar2/ar : ar/ar2;
			let tileSz = ar > ar2 ? availH/nr-TILE_SPACING : availW/nc-TILE_SPACING;
			let empSpc = (1-frac)*availW*availH + (nc*nr-numChildren)*(tileSz - TILE_SPACING)**2;
			if (empSpc < lowestEmp){
				lowestEmp = empSpc;
				numCols = nc;
				numRows = nr;
				tileSize = tileSz;
			}
		}
		let childLayouts = Array(numChildren).fill();
		for (let i = 0; i < numChildren; i++){
			let childX = TILE_SPACING + (i % numCols)*(tileSize + TILE_SPACING);
			let childY = TILE_SPACING + headerSz + Math.floor(i / numCols)*(tileSize + TILE_SPACING);
			if (node.children[i].children.length == 0){
				childLayouts[i] = {
					x: childX, y: childY, w: tileSize, h: tileSize, headerSz: 0,
					children: [],
					contentW: tileSize, contentH: tileSize, empSpc: 0,
				}
			} else {
				childLayouts[i] = this.genLayout(node.children[i], childX, childY, tileSize, tileSize, false);
				lowestEmp += childLayouts[i].empSpc;
			}
		}
		return {
			x: x, y: y, w: w, h: h, headerSz: headerSz,
			children: childLayouts,
			contentW: numCols * (tileSize + TILE_SPACING) + TILE_SPACING,
			contentH: numRows * (tileSize + TILE_SPACING) + TILE_SPACING + headerSz,
			empSpc: lowestEmp,
		}
	},
	initLayoutInfo(tree){
		return;
	},
	updateLayoutInfoOnExpand(nodeList){
		return;
	},
	updateLayoutInfoOnCollapse(nodeList){
		return;
	}
};
const staticRectLayout = {
	genLayout(node, x, y, w, h, hideHeader, subLayout = staticRectLayout){
		if (node.children.every(n => n.children.length == 0))
			return staticSqrLayout.genLayout(node, x, y, w, h, hideHeader);
		//find grid-arrangement with lowest leftover empty space
		let headerSz = (hideHeader ? 0 : HEADER_SZ);
		let availW = w - TILE_SPACING, availH = h - TILE_SPACING - headerSz;
		let numChildren = node.children.length;
		let rowBrks = null; //will holds node indices at which each row starts
		let lowestEmp = Number.POSITIVE_INFINITY, rowBreaks, rowsOfCounts, childLayouts;
		rowBrksLoop:
		while (true){
			//update rowBrks or exit loop
			if (rowBrks == null){
				rowBrks = [0];
			} else {
				let i = rowBrks.length-1;
				while (true){
					if (i > 0 && rowBrks[i] < numChildren-1 - (rowBrks.length-1 - i)){
						rowBrks[i]++;
						break;
					} else if (i > 0){
						i--;
					} else {
						if (rowBrks.length < numChildren){
							rowBrks = Array.from({length: rowBrks.length+1}, (x,i) => i);
						} else {
							break rowBrksLoop;
						}
						break;
					}
				}
			}
			//create list-of-lists representing each row's cells' tileCounts
			let rowsOfCnts = Array(rowBrks.length).fill();
			for (let r = 0; r < rowBrks.length; r++){
				let numNodes = (r == rowBrks.length-1) ? numChildren-rowBrks[r] : rowBrks[r+1]-rowBrks[r];
				let rowNodeIdxs = Array.from({length: numNodes}, (x,i) => i+rowBrks[r]);
				rowsOfCnts[r] = rowNodeIdxs.map(idx => node.children[idx].tileCount);
			}
			//get cell dims
			let totalTileCount = node.children.map(n => n.tileCount).reduce((x,y) => x+y);
			let cellHs = rowsOfCnts.map(row => row.reduce((x, y) => x+y) / totalTileCount * availH);
			let cellWs = Array(numChildren).fill();
			for (let r = 0; r < rowsOfCnts.length; r++){
				let rowCount = rowsOfCnts[r].reduce((x,y) => x+y);
				for (let c = 0; c < rowsOfCnts[r].length; c++){
					cellWs[rowBrks[r]+c] = rowsOfCnts[r][c] / rowCount * availW;
				}
			}
			//get cell x/y coords
			let cellXs = Array(cellWs.length).fill(0);
			for (let r = 0; r < rowBrks.length; r++){
				for (let c = 1; c < rowsOfCnts[r].length; c++){
					let nodeIdx = rowBrks[r]+c;
					cellXs[nodeIdx] = cellXs[nodeIdx-1] + cellWs[nodeIdx-1];
				}
			}
			let cellYs = Array(cellHs.length).fill(0);
			for (let r = 1; r < rowBrks.length; r++){
				cellYs[r] = cellYs[r-1] + cellHs[r-1];
			}
			//get child layouts and empty-space
			let childLyts = Array(numChildren).fill(), empSpc = 0;
			for (let r = 0; r < rowBrks.length; r++){
				for (let c = 0; c < rowsOfCnts[r].length; c++){
					let nodeIdx = rowBrks[r]+c;
					let child = node.children[nodeIdx];
					let childX = cellXs[nodeIdx] + TILE_SPACING, childY = cellYs[r] + TILE_SPACING + headerSz,
						childW = cellWs[nodeIdx] - TILE_SPACING, childH = cellHs[r] - TILE_SPACING;
					if (child.children.length == 0){
						let contentSz = Math.min(childW, childH);
						childLyts[nodeIdx] = {
							x: childX, y: childY, w: contentSz, h: contentSz, headerSz: 0,
							children: [],
							contentW: contentSz, contentH: contentSz, empSpc: childW*childH - contentSz**2,
						};
					} else if (child.children.every(n => n.children.length == 0)){
						childLyts[nodeIdx] = staticSqrLayout.genLayout(child, childX, childY, childW, childH, false);
					} else {
						childLyts[nodeIdx] = subLayout.genLayout(child, childX, childY, childW, childH, false);
					}
					empSpc += childLyts[nodeIdx].empSpc;
				}
			}
			//check with best-so-far
			if (empSpc < lowestEmp){
				lowestEmp = empSpc;
				rowBreaks = [...rowBrks];
				rowsOfCounts = rowsOfCnts;
				childLayouts = childLyts;
			}
		}
		//for each row, shift empty right-space to rightmost cell
		let minEmpHorzTotal = Number.POSITIVE_INFINITY;
		for (let r = 0; r < rowBreaks.length; r++){
			let empHorzTotal = 0, leftShiftTotal = 0;
			for (let c = 0; c < rowsOfCounts[r].length - 1; c++){
				let nodeIdx = rowBreaks[r] + c;
				let empHorz = childLayouts[nodeIdx].w - childLayouts[nodeIdx].contentW;
				childLayouts[nodeIdx].w -= empHorz;
				empHorzTotal += empHorz;
				childLayouts[nodeIdx+1].x -= empHorzTotal;
			}
			childLayouts[rowBreaks[r] + rowsOfCounts[r].length - 1].w += empHorzTotal;
			if (empHorzTotal < minEmpHorzTotal)
				minEmpHorzTotal = empHorzTotal;
		}
		//shift empty bottom-space to bottom-most row
		let empVertTotal = 0;
		for (let r = 0; r < rowBreaks.length - 1; r++){
			let nodeIdxs = Array.from({length: rowsOfCounts[r].length}, (x,i) => rowBreaks[r] + i);
			nodeIdxs.forEach(idx => childLayouts[idx].y -= empVertTotal);
			let empVerts = nodeIdxs.map(idx => childLayouts[idx].h - childLayouts[idx].contentH);
			let minEmpVert = Math.min(...empVerts);
			nodeIdxs.forEach(idx => childLayouts[idx].h -= minEmpVert);
			empVertTotal += minEmpVert;
		}
		let lastRowIdx = rowBreaks.length-1;
		let lastNodeIdxs = Array.from({length: rowsOfCounts[lastRowIdx].length}, (x,i) => rowBreaks[lastRowIdx] + i);
		lastNodeIdxs.forEach(idx => childLayouts[idx].y -= empVertTotal);
		lastNodeIdxs.map(idx => childLayouts[idx].h += empVertTotal);
		//determine layout
		return {
			x: x, y: y, w: w, h: h, headerSz: headerSz,
			children: childLayouts,
			contentW: w - minEmpHorzTotal,
			contentH: h - empVertTotal,
			empSpc: lowestEmp,
		}
	},
	initLayoutInfo(tree){
		if (tree.children.length > 0){
			tree.children.forEach(e => this.initLayoutInfo(e));
		}
		this.updateLayoutInfo(tree);
	},
	updateLayoutInfoOnExpand(nodeList){ //given list of tree-nodes from expanded_child-to-parent, update layout-info
		nodeList[0].children.forEach(this.updateLayoutInfo);
		for (let node of nodeList){
			this.updateLayoutInfo(node);
		}
	},
	updateLayoutInfoOnCollapse(nodeList){ //given list of tree-nodes from child_to_collapse-to-parent, update layout-info
		for (let node of nodeList){
			this.updateLayoutInfo(node);
		}
	},
	updateLayoutInfo(tree){
		if (tree.children.length == 0){
			tree.tileCount = 1;
		} else {
			tree.tileCount = tree.children.map(e => e.tileCount).reduce((x,y) => x+y);
		}
	}
};
const sweepToSideLayout = {
	genLayout(node, x, y, w, h, hideHeader){
		//separate leaf and non-leaf nodes
		let leaves = [], nonLeaves = [];
		node.children.forEach(n => (n.children.length == 0 ? leaves : nonLeaves).push(n));
		//determine layout
		let tempTree;
		if (nonLeaves.length == 0){ //if all leaves, use squares-layout
			return staticSqrLayout.genLayout(node, x, y, w, h, hideHeader);
		} else if (leaves.length == 0){
			tempTree = {tolNode: null, children: nonLeaves};
			return staticRectLayout.genLayout(tempTree, x, y, w, h, hideHeader);
		} else {
			let ratio = leaves.length / (leaves.length + nonLeaves.map(e => e.tileCount).reduce((x,y) => x+y));
			let headerSz = (hideHeader ? 0 : HEADER_SZ);
			//get swept-area layout
			let area = {x: x, y: y+headerSz, w: w, h: h-headerSz};
			tempTree = {tolNode: null, children: leaves};
			let leftLayout = staticSqrLayout.genLayout(tempTree, area.x, area.y, area.w*ratio, area.h, true);
			let topLayout = staticSqrLayout.genLayout(tempTree, area.x, area.y, area.w, area.h*ratio, true);
			//let sweptLayout = leftLayout;
			let sweptLayout = (leftLayout.empSpc < topLayout.empSpc) ? leftLayout : topLayout;
			sweptLayout.children.forEach(layout => {layout.y += headerSz});
			//get remaining-area layout
			let xyChg;
			if (sweptLayout == leftLayout){
				xyChg = [sweptLayout.contentW - TILE_SPACING, 0];
				area.w += -sweptLayout.contentW + TILE_SPACING;
			} else {
				xyChg = [0, sweptLayout.contentH - TILE_SPACING];
				area.h += -sweptLayout.contentH + TILE_SPACING;
			}
			tempTree = {tolNode: null, children: nonLeaves}
			let nonLeavesLayout = staticRectLayout.genLayout(
				tempTree, area.x, area.y, area.w, area.h, true, sweepToSideLayout);
			nonLeavesLayout.children.forEach(layout => {layout.x += xyChg[0]; layout.y += xyChg[1] + headerSz;});
			//return combined layouts
			let children = leaves.concat(nonLeaves);
			let layouts = sweptLayout.children.concat(nonLeavesLayout.children);
			let layoutsInOldOrder = [...Array(node.children.length).keys()]
				.map(i => children.findIndex(n => n == node.children[i]))
				.map(i => layouts[i]);
			return {
				x: x, y: y, w: w, h: h, headerSz: headerSz,
				//children: [...sweptLayout.children, ...nonLeavesLayout.children],
				children: layoutsInOldOrder,
				contentW: (sweptLayout == leftLayout) ?
					sweptLayout.contentW + nonLeavesLayout.contentW - TILE_SPACING :
					Math.max(sweptLayout.contentW, nonLeavesLayout.contentW),
				contentH: (sweptLayout == leftLayout) ?
					Math.max(sweptLayout.contentH, nonLeavesLayout.contentH) :
					sweptLayout.contentH + nonLeavesLayout.contentH - TILE_SPACING,
				empSpc: sweptLayout.empSpc + nonLeavesLayout.empSpc
			};
		}
	},
	initLayoutInfo(tree){
		if (tree.children.length > 0){
			tree.children.forEach(e => this.initLayoutInfo(e));
		}
		this.updateLayoutInfo(tree);
	},
	updateLayoutInfoOnExpand(nodeList){
		nodeList[0].children.forEach(this.updateLayoutInfo);
		for (let node of nodeList){
			this.updateLayoutInfo(node);
		}
	},
	updateLayoutInfoOnCollapse(nodeList){
		for (let node of nodeList){
			this.updateLayoutInfo(node);
		}
	},
	updateLayoutInfo(tree){
		if (tree.children.length == 0){
			tree.tileCount = 1;
		} else {
			tree.tileCount = tree.children.map(e => e.tileCount).reduce((x,y) => x+y);
		}
	}
};

