#include <iostream>
#include <fstream>
#include "nlohmann/json.hpp"
#include <zip.h>
#define MD5_IMPLEMENTATION
#include "md5.h"
using namespace std;
using namespace filesystem;
#define cfg_path "..\\cfg.json"
using json = nlohmann::json;
struct game_data{
    string game_path;
    string name;
};
NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(game_data, name, game_path)

struct Games_cfg{
    vector <game_data> games;
};

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(Games_cfg, games)

bool save_cfg(Games_cfg Games){
        ofstream ofs (cfg_path);
        if (!ofs.is_open()){
                cout << "Error of opening cfg file";
                return false;
        }
        json j = Games;
        ofs << j.dump(2);
        ofs.close();
        return true;
}

Games_cfg load_cfg(){
        std::ifstream ifs(cfg_path);
        if (ifs.is_open()){
                json j;
                ifs >> j;
                ifs.close();
                return Games_cfg(j);
        }
        else{  cout << "Error of opening cfg file";  return Games_cfg();  }

}

string get_file_md5(const path& filepath) {
        std::ifstream file(filepath, std::ios::binary);
        if (!file.is_open()) return "";

        MD5 md5;
        char buffer[8192];

        while (file.read(buffer, sizeof(buffer))) {
                md5.update(reinterpret_cast<uint8_t*>(buffer), file.gcount());
        }
        if (file.gcount() > 0) {
                md5.update(reinterpret_cast<uint8_t*>(buffer), file.gcount());
        }
        md5.finalize();
        return md5.toString();
}

int main(){
        Games_cfg games = load_cfg();
        const string apdt_path = getenv("LOCALAPPDATA");
        path arc_path = path(apdt_path) / "GameSaves";
        create_directory(arc_path);
        for (game_data n : games.games){
                path pth = arc_path / n.name;
                create_directory(pth);
                for (const auto& entry : directory_iterator(n.game_path.c_str())) {
                    if (entry.is_regular_file()) {
                        string md5 = get_file_md5(entry.path());
                        string orig_name = entry.path().filename().string();
                        path zip_path = pth / (md5 + ".zip");
                        struct zip_t* zip = zip_open(zip_path.u8string().c_str(), 6, 'w');
                        zip_entry_open(zip, orig_name.c_str());
                        zip_entry_fwrite(zip, entry.path().u8string().c_str());
                        zip_entry_close(zip);
                        zip_close(zip);
                    }
                }
        }
}
