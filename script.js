const fs = require('node:fs/promises');
const pako = require('pako');

async function gatherDataPrimitive(path, data, people) {
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

            if (content.includes("category: people") || content.includes("category: reference") || content.includes("category: meta") ||
                content.includes("category:people") || content.includes("category:reference") || content.includes("category:meta")
                || content.includes("[[!include physicscontents]]")
                || content.includes("[[!include fields and quanta - table]]")
// cannot exclude the following
//                || content.includes("[[!include functorial quantum field theory - contents]]")
//                || content.includes("[[!include AQFT and operator algebra contents]]")
) {
                // person article
                for (let alt of alts) {
                    people.add(alt);
                }
                people.add(name);
            } else {
                // real article
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
            }
        } else if (file.isDirectory()) {
            await gatherDataPrimitive(filepath, data, people);
        }
    })()));
}

async function gatherData(path, data) {
    let people = new Set();
    await gatherDataPrimitive(path, data, people);

    console.log("Remove people...");

    for (let article in data) {
        if (data[article].links) {
            data[article].links = data[article].links.filter(name => !people.has(name));
        }
    }
}

let data = {};
(async function() {
    await gatherData("./nlab-content", data);
    await fs.writeFile("data.bin", pako.deflate(new TextEncoder().encode(JSON.stringify(data))));
})();
