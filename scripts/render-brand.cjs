// Prepare HA's standard icon sizes from the unchanged HomeBuddy artwork.
// macOS build helper; generated PNGs are committed, so installation needs no tools.
const {execFileSync}=require('node:child_process');
const path=require('node:path');
const root=path.resolve(__dirname,'../custom_components/homebuddy_access');
for(const name of ['icon.png','icon@2x.png','logo.png','logo@2x.png','dark_logo.png','dark_logo@2x.png']){
 const size=name.includes('@2x')?'512':'256';
 execFileSync('sips',['-z',size,size,path.join(root,'www/logo.png'),'--out',path.join(root,'brand',name)],{stdio:'ignore'});
}
