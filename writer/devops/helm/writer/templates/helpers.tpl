{{- define "appName.name" -}}
{{- if (.Values.server.nameprefix) -}}
{{- printf "%s-%s" .Values.server.nameprefix .Values.server.name -}}
{{- else -}}
{{- printf "%s" .Values.server.name -}}
{{- end -}}
{{- end -}}
