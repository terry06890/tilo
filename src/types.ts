export class TolNode {
	name: string;
	children: TolNode[];
	constructor(name: string, children: TolNode[] = []){
		this.name = name;
		this.children = children;
	}
}
export class LayoutNode {
	//set by TileTree and LayoutFn funcs, eventually used by Tile
	tolNode: TolNode;
	children: LayoutNode[];
	x: number;
	y: number;
	w: number;
	h: number;
	headerSz: number;
	//set by layoutInfoHooks, used by LayoutFn funcs
	tileCount: number;
	//set_by/internal_to LayoutFn funcs
	contentW: number;
	contentH: number;
	empSpc: number;
	//set by LayoutFn funcs, eventually used by Tile
	sepSweptArea: SepSweptArea | null;
	//
	constructor(tolNode: TolNode, children: LayoutNode[], x=0, y=0, w=0, h=0,
		{headerSz=0, tileCount=0, contentW=0, contentH=0, empSpc=0, sepSweptArea=null as SepSweptArea|null} = {}){
		this.tolNode = tolNode;
		this.children = children;
		this.x = x;
		this.y = y;
		this.w = w;
		this.h = h;
		this.headerSz = headerSz;
		this.tileCount = tileCount;
		this.contentW = contentW;
		this.contentH = contentH;
		this.empSpc = empSpc;
		this.sepSweptArea = sepSweptArea;
	}
}
export class SepSweptArea {
	x: number;
	y: number;
	w: number;
	h: number;
	sweptLeft: boolean;
	tileSpacing: number;
	constructor(x: number, y: number, w: number, h: number, sweptLeft: boolean, tileSpacing: number){
		this.x = x;
		this.y = y;
		this.w = w;
		this.h = h;
		this.sweptLeft = sweptLeft;
		this.tileSpacing = tileSpacing;
	}
}
