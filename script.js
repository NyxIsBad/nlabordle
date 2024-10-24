const fs = require('node:fs/promises');
const pako = require('pako');

async function gatherData(path, data) {
    const files = await fs.readdir(path, {withFileTypes: true});
    await Promise.all(files.map(file => (async function() {
        let filepath = path + "/" + file.name;
        let nameExists = false;
        try {
            await fs.stat(filepath + "/name");
            nameExists = true;
        } catch(err) {}
        if (nameExists) {
            let name = await fs.readFile(filepath + "/name", {encoding: "utf-8"});
            let content = await fs.readFile(filepath + "/content.md", { encoding: "utf-8" });
            let links = (content.match(/\[\[[A-Za-z0-9_\-\s]+\]\]/g) || []).map(c => c.slice(2, -2));
            let alts = [];

            let r = /\[\[\!redirects ([A-Za-z0-9\-_\s]+)\]\]/g;
            for(;;) { 
                match = r.exec(content);
                if (match == null) break;
                alts.push(match[1]);
            }

            for (let alt of alts) {
                data[alt] = {
                    redirect: name
                }
            };
            data[name] = {
                links: links,
                alts: alts,
                content: content,
            };

        } else if (file.isDirectory()) {
            await gatherData(filepath, data);
        }
    })()));
}

let data = {};
(async function() {
    await gatherData("./nlab-content", data);
    await fs.writeFile("data.bin", pako.deflate(new TextEncoder().encode(JSON.stringify(data))));
})();
