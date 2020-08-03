#include "CSCfgTables.h"
#include "BufferReader.hpp"
#include "CSCfgVersion.h"
#include "ConfigUtil.h"
#include <network/util/file.hpp>

GameServerVersion G_SERVER_VERSION = Server_Flamen;

namespace GameConfig
{
    CSCfgTables::CSCfgTables()
    {

    }

    int CSCfgTables::Init(const char* filepath)
    {
        string content = cytx::file_util::read_all(filepath);

        int ret = Init(content.data(), (int)content.size());
        if(ret != 0)
        {
            std::cout << "load config failed" << std::endl;
        }
        return 0;
    }

    int CSCfgTables::Init(const char* buffer, int length)
    {
        auto stream = MemoryStream(buffer, length);
        std::string versionStr;
        stream.ReadString(versionStr);
        std::cout << "data version: " << versionStr << std::endl;

        const int total_table_count = ${all.sheets_count};
        int read_table_count = 0;

        while(read_table_count < total_table_count && !stream.IsEnd())
        {
            std::string table_name;
            uint32_t count = 0;
            uint32_t byte_length = 0;
            stream.ReadTableBegin(table_name, count, byte_length);
            % for i, sheet in enumerate(all.sheets):
            % for j, sub_sheet in enumerate(sheet.sub_sheets):
            % if i == 0:
            if (table_name == "${sub_sheet.name}")
            % else:
            else if (table_name == "${sub_sheet.name}")
            % endif
            {
                ++read_table_count;
                INT32 battleType = ToBattleType(${sub_sheet.config_type});
                for(uint32_t i = 0; i< count; ++i)
                {
                    % if not sheet.single:
                    ${sheet.name} item;
                    item.read(stream);
                    onLoad${sheet.name}(item, battleType);
                    ${sub_sheet.member_name}[item.${sheet.key_field.name}] = item;
                    % else:
                    ${sub_sheet.member_name}.read(stream);
                    onLoad${sheet.name}(${sub_sheet.member_name}, battleType);
                    % endif
                }
                stream.ReadTableEnd();
            }
            % endfor
            % endfor
            // no this table, so skip
            else
            {
                stream.Consume(byte_length);
            }
        }

        if (read_table_count < total_table_count)
        {
            std::cout << fmt::format("total {} tables, but only read {} tables", total_table_count, read_table_count) << std::endl;
            return 1;
        }

        return 0;
    }

    INT32 CSCfgTables::ToConfigType(INT32 battleType)
    {
        if (battleType == EBT_MOBA)
            return 1;
        else if(battleType == EBT_DIAMOND)
            return 2;
        else if(battleType == EBT_FLY)
            return 3;

        return 0;
    }

    INT32 CSCfgTables::ToBattleType(INT32 configType)
    {
        if (configType == 1)
            return EBT_MOBA;
        else if(configType == 2)
            return EBT_DIAMOND;
        else if(configType == 3)
            return EBT_FLY;

        return EBT_PVP;
    }

    % for sheet in all.singles:
    % if len(sheet.sub_sheets) <= 1:
    const ${sheet.name}* CSCfgTables::Get${sheet.short_name}()
    {
        return &${sheet.member_name};
    }
    % else:
    const ${sheet.name}* CSCfgTables::Get${sheet.short_name}(INT32 type)
    {
        INT32 configType = ToConfigType(type);
        if (configType == 1)
        {
            return &${sheet.get_sub_sheet_by_config_type(1).member_name};
        }
        else if(configType == 2)
        {
            return &${sheet.get_sub_sheet_by_config_type(2).member_name};
        }
        else if(configType == 3)
        {
            return &${sheet.get_sub_sheet_by_config_type(3).member_name};
        }

        return &${sheet.get_sub_sheet_by_config_type(0).member_name};
    }
    % endif
    % endfor

    % for sheet in all.not_singles:
    % if len(sheet.sub_sheets) <= 1:
    const ${sheet.name}* CSCfgTables::Get${sheet.short_name}(UINT32 Id)
    {
        auto it = ${sheet.member_name}.find(Id);
        if(it != ${sheet.member_name}.end())
        {
            return &it->second;
        }
        return nullptr;
    }
    % else:
    const ${sheet.name}* CSCfgTables::Get${sheet.short_name}(UINT32 Id, INT32 type)
    {
        INT32 configType = ToConfigType(type);
        auto pConfigMap = &${sheet.get_sub_sheet_by_config_type(0).member_name};
        if(configType == 1)
        {
            pConfigMap = &${sheet.get_sub_sheet_by_config_type(1).member_name};
        }
        else if(configType == 2)
        {
            pConfigMap = &${sheet.get_sub_sheet_by_config_type(2).member_name};
        }
        else if(configType == 3)
        {
            pConfigMap = &${sheet.get_sub_sheet_by_config_type(3).member_name};
        }
        auto it = pConfigMap->find(Id);
        if(it != pConfigMap->end())
        {
            return &it->second;
        }
        return nullptr;
    }
    % endif
    % endfor
}