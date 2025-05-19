import logging

from sankhya_api.auth import SankhyaClient
from sankhya_api.utils import execute_query


# ============================================================
# ITENS DA TAREFA                                            =
# ============================================================


def snk_fetch_itens_tarefa(nunota, client: SankhyaClient):
    sql = f"""
            SELECT 
                LTRIM(RTRIM(STR(ITE.CODPROD)))+'-'+LTRIM(RTRIM(STR(CAB.NUNOTA)))+'-'+LTRIM(RTRIM(STR(CAB.NUMNOTA)))+'-'+LTRIM(STR(ABS(CHECKSUM(NewId())) % 99999)) AS alternativeidentifier, 
                PRO.DESCRPROD AS description, 
                1 AS active, 
                CASE WHEN CAB.CODTIPOPER=1264 THEN 'prod' WHEN CAB.CODTIPOPER=1280 THEN 'assist' ELSE 'tec' END AS subgroup, 
                ITE.QTDNEG AS qtd_item, 
                CAB.NUNOTA AS num_pedido 
            FROM TGFCAB CAB, TGFITE ITE, TGFPRO PRO 
            WHERE CAB.NUNOTA = ITE.NUNOTA AND ITE.CODPROD = PRO.CODPROD AND CAB.NUNOTA = {nunota} AND ITE.AD_MONTAGEM = 'S'
        """
    rows = execute_query(sql, client)
    itens_tarefa = []
    for row in rows:
        itens_tarefa.append(row)
    return itens_tarefa


# ============================================================
# LOCAL DA TAREFA                                            =
# ============================================================


def snk_fetch_local_tarefa(nunota, client: SankhyaClient):
    sql = f"""
            SELECT 
                TOP 1 LTRIM(RTRIM(STR(CAB.CODPARC)))+'-'+LTRIM(RTRIM(STR(CAB.NUNOTA)))+ '-' +LTRIM(RTRIM(STR(CAB.NUMNOTA)))  AS alternativeidentifier, 
                RTRIM(PAR.NOMEPARC) + '-' +  LTRIM(STR(CAB.CODPARC)) + '-' + LTRIM(STR(CAB.NUNOTA)) AS description, 
                RTRIM(PAR.RAZAOSOCIAL) + '-' + RTRIM(LTRIM(STR(CAB.CODPARC)) + '-' + LTRIM(STR(CAB.NUNOTA))) AS corporateName,
                CASE WHEN PAR.ATIVO = 'S' THEN 1 ELSE 0 END AS active,
                ISNULL(RTRIM(PAR.EMAIL),'casacontente@casacontente.com.br') AS email,
                REPLACE(RTRIM(PAR.TELEFONE), ' ', '') AS cellphoneStd,
                'BRASIL' AS country,
                (SELECT RTRIM(CID.NOMECID) FROM TSICID CID WHERE CID.CODCID = CPL.CODCIDENTREGA) AS state,
                (SELECT RTRIM(DESCRICAO) FROM TSIUFS WHERE CODUF = (SELECT CID.UF FROM TSICID CID WHERE CID.CODCID = CPL.CODCIDENTREGA)) AS city,
                (SELECT RTRIM(BAI.NOMEBAI) FROM TSIBAI BAI WHERE BAI.CODBAI = CPL.CODBAIENTREGA) AS cityNeighborhood,
                (SELECT RTRIM(RUA.TIPO) + ' ' + RTRIM(RUA.NOMEEND) FROM TSIEND RUA WHERE RUA.CODEND = CPL.CODENDENTREGA) + ', ' + ISNULL(RTRIM(LTRIM(STR( CASE WHEN NUMENTREGA LIKE '%SN%' THEN 0 ELSE SUBSTRING(NUMENTREGA, PATINDEX('%[0-9]%', NUMENTREGA), PATINDEX('%[0-9][^0-9]%', NUMENTREGA + 't') - PATINDEX('%[0-9]%', NUMENTREGA) + 1) END ))),0) AS street,
                CPL.CEPENTREGA AS zipcode  
            FROM TGFCAB CAB, TGFPAR PAR, TGFITE ITE, TGFCPL CPL 
            WHERE  CAB.CODPARC = PAR.CODPARC AND PAR.CODPARC = CPL.CODPARC AND CAB.NUNOTA = ITE.NUNOTA 
                AND CODTIPOPER in (1264, 1247, 1280)   AND CAB.NUNOTA = {nunota}  AND ITE.AD_MONTAGEM = 'S'
        """
    rows = execute_query(sql, client)
    itens_tarefa = []
    for row in rows:
        itens_tarefa.append(row)
    return itens_tarefa


# ============================================================
# TAREFA                                                     =
# ============================================================

def snk_fetch_tarefa(nunota, client: SankhyaClient):
    sql = f"""
            SELECT TOP 1 
              LTRIM(STR(CAB.NUMNOTA)) + '-' + LTRIM(STR(ABS(CHECKSUM(NewId())) % 99999)) AS alternativeIdentifier, 
              LTRIM(RTRIM(STR(CAB.CODPARC))) + '-' + LTRIM(RTRIM(STR(CAB.NUNOTA))) + '-' + LTRIM(RTRIM(STR(CAB.NUMNOTA))) AS serviceLocal, 
              RTRIM(ISNULL((SELECT CGC_CPF FROM TGFPAR WHERE CODPARC = (SELECT CODPARC FROM TGFVEN WHERE CODVEND = CAB.AD_MONTADOR)), 'master')) AS agent, 
              'Montagem Internos' AS scheduleType, 
              CONVERT(varchar(10), GETDATE()+1, 103) AS date, 
              7 AS activitiesOrigin, 
              NULL AS hour, 
              CASE 
                WHEN (SELECT CODTIPOPER FROM TGFCAB WHERE NUNOTA =  {nunota} ) <> 1264 THEN 'VISITA TÉCNICA - ' ELSE '' END 
                + '' + (SELECT TELEFONE + '/' + FAX FROM TGFPAR WHERE CODPARC = (SELECT CODPARC FROM TGFCAB WHERE NUNOTA = {nunota})) 
                + ' - ' + (SELECT string_agg(PRODUTO, ', ') within group (order by PRODUTO) as PRODUTOS FROM (SELECT SUBSTRING(DESCRPROD,1,(CHARINDEX(' ',DESCRPROD + ' ')-1)) +' '+ AD_MODELOREF +' '+ MARCA  [PRODUTO] FROM TGFPRO WHERE CODPROD IN (SELECT CODPROD FROM TGFITE WHERE NUNOTA = {nunota} AND AD_MONTAGEM = 'S')) AS D) 
                + ' - ' + (SELECT RTRIM(BAI.NOMEBAI) 
                + ', ' + RUA.TIPO 
                + ' ' +  RUA.NOMEEND 
                + ' ' + RTRIM(CPL.NUMENTREGA) 
                + ', ' + RTRIM(CPL.COMPLENTREGA) 
                + ', ' + REPLACE(CPL.LOGISTICA, '//',',') 
              FROM TGFCPL CPL, TSIEND RUA, TSIBAI BAI WHERE CPL.CODENDENTREGA = RUA.CODEND AND CPL.CODBAIENTREGA = BAI.CODBAI AND CPL.CODPARC = CAB.CODPARC) AS observation, 
              CAB.NUNOTA AS N_pedido,
              CASE 
                WHEN CAB.CODTIPOPER = 1264 THEN 'montagem'
                WHEN CAB.CODTIPOPER = 1247 THEN 'visitatec'
                WHEN CAB.CODTIPOPER = 1280 THEN 'assistencia' 
              END AS [CF_tipo_servico] 
            FROM TGFCAB CAB, TGFITE ITE  
            WHERE CAB.NUNOTA = ITE.NUNOTA AND ITE.AD_MONTAGEM = 'S' AND CAB.NUNOTA =  {nunota}
        """
    rows = execute_query(sql, client)
    itens_tarefa = []
    for row in rows:
        itens_tarefa.append(row)
    return itens_tarefa
