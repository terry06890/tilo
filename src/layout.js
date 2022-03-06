export {defaultLayout, initTree};

const DEFAULT_TILE_SPACING = 5;
const DEFAULT_HEADER_SZ = 20;

const staticSqrLayout = { //determines layout for squares in a specified rectangle, with spacing
	TILE_SPACING: DEFAULT_TILE_SPACING,
	HEADER_SZ: DEFAULT_HEADER_SZ,
	genLayout(nodes, x0, y0, w, h, hideHeader){
		//get number-of-columns with highest occupied-fraction of rectangles with aspect-ratio w/h
			//account for tile-spacing?, account for parent-box-border?, cache results?,
		let hOffset = (hideHeader ? 0 : this.HEADER_SZ);
		let numTiles = nodes.length, ar = (w - this.TILE_SPACING)/(h - hOffset - this.TILE_SPACING);
		let numCols, numRows, bestFrac = 0;
		for (let nc = 1; nc <= numTiles; nc++){
			let nr = Math.ceil(numTiles/nc);
			let ar2 = nc/nr;
			let frac = ar > ar2 ? ar2/ar : ar/ar2;
			if (frac > bestFrac){
				bestFrac = frac;
				numCols = nc;
				numRows = nr;
			}
		}
		//compute other parameters
		let tileSz = Math.min(
			((w - this.TILE_SPACING) / numCols) - this.TILE_SPACING,
			((h - this.TILE_SPACING - hOffset) / numRows) - this.TILE_SPACING);
		//determine layout
		return {
			coords: Object.fromEntries(
				nodes.map((el, idx) => [el.tolNode.name, {
					x: x0 + this.TILE_SPACING + (idx % numCols)*(tileSz + this.TILE_SPACING),
					y: y0 + this.TILE_SPACING + hOffset + Math.floor(idx / numCols)*(tileSz + this.TILE_SPACING),
					w: tileSz,
					h: tileSz
				}])
			),
			w: numCols * (tileSz + this.TILE_SPACING) + this.TILE_SPACING,
			h: numRows * (tileSz + this.TILE_SPACING) + this.TILE_SPACING + hOffset,
		};
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
	TILE_SPACING: DEFAULT_TILE_SPACING,
	HEADER_SZ: DEFAULT_HEADER_SZ,
	genLayout(nodes, x0, y0, w, h, hideHeader){
		if (nodes.every(e => e.children.length == 0)){
			return staticSqrLayout.genLayout(nodes, x0, y0, w, h, hideHeader);
		}
		//if a node has children, find 'best' grid-arrangement
		let hOffset = (hideHeader ? 0 : this.HEADER_SZ);
		let availW = w - this.TILE_SPACING, availH = h - this.TILE_SPACING - hOffset;
		let numChildren = nodes.length;
		let rowBrks = [0]; //holds node indices at which each row starts
		let rowBreaks, bestScore = Number.NEGATIVE_INFINITY, rowsOfCounts, cellWidths, cellHeights, nodeDims;
		while (true){
			//create list-of-lists representing each row's cells' tileCounts
			let rowsOfCnts = Array(rowBrks.length).fill();
			for (let r = 0; r < rowBrks.length; r++){
				let numNodes = (r == rowBrks.length-1) ? numChildren-rowBrks[r] : rowBrks[r+1]-rowBrks[r];
				let rowNodeIdxs = Array.from({length: numNodes}, (x,i) => i+rowBrks[r]);
				rowsOfCnts[r] = rowNodeIdxs.map(idx => nodes[idx].tileCount);
			}
			//get cell dims
			let totalTileCount = nodes.map(e => e.tileCount).reduce((x,y) => x+y);
			let cellHs = rowsOfCnts.map(row => row.reduce((x, y) => x+y) / totalTileCount * availH);
			let cellWs = Array(numChildren).fill();
			for (let r = 0; r < rowsOfCnts.length; r++){
				let rowCount = rowsOfCnts[r].reduce((x,y) => x+y);
				for (let c = 0; c < rowsOfCnts[r].length; c++){
					cellWs[rowBrks[r]+c] = rowsOfCnts[r][c] / rowCount * availW;
				}
			}
			//get node dims and score
			let score = 0;
			let nodeDs = Array(numChildren).fill();
			for (let r = 0; r < rowBrks.length; r++){
				for (let c = 0; c < rowsOfCnts[r].length; c++){
					let nodeIdx = rowBrks[r]+c;
					let cellW = cellWs[nodeIdx], cellH = cellHs[r];
					let ar = (cellW - this.TILE_SPACING) / (cellH - this.TILE_SPACING);
					let ar2 = nodes[nodeIdx].arFromArea(cellW - this.TILE_SPACING, cellH - this.TILE_SPACING);
					let frac = ar > ar2 ? ar2/ar : ar/ar2;
					score += frac * (cellW * cellH);
					nodeDs[nodeIdx] = ar > ar2 ? [cellW*frac, cellH] : [cellW, cellH*frac];
				}
			}
			if (score > bestScore){
				bestScore = score;
				rowBreaks = [...rowBrks];
				rowsOfCounts = rowsOfCnts;
				cellWidths = cellWs;
				cellHeights = cellHs;
				nodeDims = nodeDs;
			}
			//update rowBrks or exit loop
			let i = rowBrks.length-1, exitLoop = false;
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
						exitLoop = true;
					}
					break;
				}
			}
			if (exitLoop)
				break;
		}
		//for each row, shift empty right-space to rightmost cell
		for (let r = 0; r < rowBreaks.length; r++){
			let empHorzTotal = 0;
			for (let c = 0; c < rowsOfCounts[r].length - 1; c++){
				let nodeIdx = rowBreaks[r] + c;
				let empHorz = cellWidths[nodeIdx] - nodeDims[nodeIdx][0];
				cellWidths[nodeIdx] -= empHorz;
				empHorzTotal += empHorz;
			}
			cellWidths[rowBreaks[r] + rowsOfCounts[r].length - 1] += empHorzTotal;
		}
		//shift empty bottom-space to bottom-most row
		let empVertTotal = 0;
		for (let r = 0; r < rowBreaks.length - 1; r++){
			let nodeIdxs = Array.from({length: rowsOfCounts[r].length}, (x,i) => rowBreaks[r] + i);
			let empVerts = nodeIdxs.map(idx => cellHeights[r] - nodeDims[idx][1]);
			let minEmpVert = Math.min(...empVerts);
			cellHeights[r] -= minEmpVert;
			empVertTotal += minEmpVert;
		}
		cellHeights[rowBreaks.length - 1] += empVertTotal;
		//determine layout
		let cellHorzPoints = Array(cellWidths.length).fill(0);
		for (let r = 0; r < rowBreaks.length; r++){
			for (let c = 1; c < rowsOfCounts[r].length; c++){
				let nodeIdx = rowBreaks[r]+c;
				cellHorzPoints[nodeIdx] = cellHorzPoints[nodeIdx-1] + cellWidths[nodeIdx-1];
			}
		}
		let cellVertPoints = Array(cellHeights.length).fill(0);
		for (let r = 1; r < rowBreaks.length; r++){
			cellVertPoints[r] = cellVertPoints[r-1] + cellHeights[r-1];
		}
		return {
			coords: Object.fromEntries(
				nodes.map((el, idx) => {
					let cellW = cellWidths[idx];
					let rowIdx = rowBreaks.findIndex((e,i) => i==rowBreaks.length-1 || rowBreaks[i+1] > idx);
					let cellH = cellHeights[rowIdx];
					let cellAR = cellW / cellH;
					return [el.tolNode.name, {
						x: x0 + this.TILE_SPACING + cellHorzPoints[idx],
						y: y0 + this.TILE_SPACING + cellVertPoints[rowIdx] + hOffset,
						w: (el.children.length == 0 ? (cellAR>1 ? cellW * 1/cellAR : cellW) : cellW) - this.TILE_SPACING,
						h: (el.children.length == 0 ? (cellAR>1 ? cellH : cellH * cellAR) : cellH) - this.TILE_SPACING
					}];
				})
			),
			w: w,
			h: h,
		};
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
			tree.arFromArea = (w, h) => 1;
		} else {
			tree.tileCount = tree.children.map(e => e.tileCount).reduce((x,y) => x+y);
			if (tree.children.every(e => e.children.length == 0)){
				tree.arFromArea = (w, h) => {
					let layout = staticSqrLayout.genLayout(tree.children, 0, 0, w, h, tree.hideHeader);
					return layout.w / layout.h;
				}
			} else {
				tree.arFromArea = (w, h) => w/h;
			}
		}
	}
};
const sweepToSideLayout = {
	TILE_SPACING: DEFAULT_TILE_SPACING,
	HEADER_SZ: DEFAULT_HEADER_SZ,
	genLayout(nodes, x0, y0, w, h, hideHeader){
		//separate leaf and non-leaf nodes
		let leaves = [], nonLeaves = [];
		nodes.forEach(e => (e.children.length == 0 ? leaves : nonLeaves).push(e));
		//determine layout
		if (nonLeaves.length == 0){ //if all leaves, use squares-layout
			return staticSqrLayout.genLayout(nodes, x0, y0, w, h, hideHeader);
		} else { //if some non-leaves, use rect-layout
			if (leaves.length == 0){
				return staticRectLayout.genLayout(nonLeaves, x0, y0, w, h, hideHeader);
			} else {
				//get swept-area layout
				let ratio = leaves.length / (leaves.length + nonLeaves.map(e => e.tileCount).reduce((x,y) => x+y));
				let leavesLayout = staticSqrLayout.genLayout(leaves, x0, y0, w*ratio, h, hideHeader);
				//get remaining-area layout, with shrunk-to-content-right-edge swept-area
				let x02 = x0 + leavesLayout.w - this.TILE_SPACING;
				let w2 = w - leavesLayout.w + this.TILE_SPACING;
				//let nonLeavesLayout = staticSqrLayout.genLayout(nonLeaves, x02, y0, w2, h, hideHeader);
				let nonLeavesLayout = staticRectLayout.genLayout(nonLeaves, x02, y0, w2, h, hideHeader);
				return {coords: {...leavesLayout.coords, ...nonLeavesLayout.coords}, w: w, h: h}
			}
		}
	},
	initLayoutInfo(tree){
		staticRectLayout.initLayoutInfo(tree);
	},
	updateLayoutInfoOnExpand(nodeList){
		staticRectLayout.updateLayoutInfoOnExpand(nodeList);
	},
	updateLayoutInfoOnCollapse(nodeList){
		staticRectLayout.updateLayoutInfoOnCollapse(nodeList);
	}
};
let defaultLayout = sweepToSideLayout;

function initTree(tol, lvl, layout = defaultLayout){
	let tree = {tolNode: tol, children: []};
	initTreeRec(tree, lvl);
	layout.initLayoutInfo(tree)
	return tree;
}
function initTreeRec(tree, lvl){
	if (lvl > 0){
		tree.children = tree.tolNode.children.map(e => initTreeRec({tolNode: e, children: []}, lvl-1));
	}
	return tree;
}
