#pragma once
#include "CSCfgTypes.h"

using namespace std;

namespace GameConfig
{
    class CSCfgTables
    {
    public:
        CSCfgTables();

        int Init(const char* filepath);
        int Init(const char* buffer, int length);

    public:
        % for sheet in all.singles:
        % if len(sheet.sub_sheets) <= 1:
        const ${sheet.name}* Get${sheet.short_name}();
        % else:
        const ${sheet.name}* Get${sheet.short_name}(INT32 type);
        % endif
        % endfor

        % for sheet in all.not_singles:
        % if len(sheet.sub_sheets) <= 1:
        const ${sheet.name}* Get${sheet.short_name}(UINT32 Id);
        % else:
        const ${sheet.name}* Get${sheet.short_name}(UINT32 Id, INT32 type);
        % endif
        % endfor

    protected:
        virtual INT32 ToConfigType(INT32 battleType);
        virtual INT32 ToBattleType(INT32 configType);

        % for sheet in all.sheets:
        virtual void onLoad${sheet.name}(${sheet.name}& item, INT32 battleType) {}
        % endfor

    public:
        % for sheet in all.singles:
        % for sub_sheet in sheet.sub_sheets:
        ${sheet.name} ${sub_sheet.member_name};
        % endfor
        % endfor

        % for sheet in all.not_singles:
        % for sub_sheet in sheet.sub_sheets:
        map<${sheet.key_field.type_name}, ${sheet.name}> ${sub_sheet.member_name};
        % endfor
        % endfor
    };
}