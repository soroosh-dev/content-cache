local _M = {}
function _M.get_filename(response)
    local json = require "cjson"
    local done, response_dict = pcall(json.decode, tostring(response))
    if done then
        ngx.shared.filename_dict:set(ngx.ctx.request_id, response_dict['filename'])
    end
end

return _M
