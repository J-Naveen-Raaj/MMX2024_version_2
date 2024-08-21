import datetime

import pandas as pd


class SpendChangeHandler(object):
    def __init__(self, spend_scenario_details):
        self.df = pd.DataFrame.from_records(spend_scenario_details)


    def HigherleveltpsReturnString(self, x,get_year): # Higher time period_name's
        if x in ['Jan', 'Feb', 'Mar']:
            return 'Q1'
        if x in ['Apr', 'May', 'Jun']:
            return 'Q2'
        if x in ['Jul', 'Aug', 'Sep']:
            return 'Q3'
        if x in ['Oct', 'Nov', 'Dec']:
            return 'Q4'
        if x in ['Q1', 'Q2']:
            return 'H1'
        if x in ['Q3', 'Q4']:
            return 'H2'
        if x in ['H1', 'H2']:
            return 'Year'
        if x == 'Year':
            return []
        no_of_weeks = self.noofweeks(get_year)
        d2=dict()
        for i in no_of_weeks.values():
            d2[list(i)[0].title()]=[]
        for i in no_of_weeks.items():
            d2[list(i[1])[0].title()].append(i[0])
        if x in d2["Jan"]:
            return 'Jan'
        if x in d2["Feb"]:
            return 'Feb'
        if x in d2["Mar"]:
            return 'Mar'
        if x in d2["Apr"]:
            return 'Apr'
        if x in d2["May"]:
            return 'May'
        if x in d2["Jun"]:
            return 'Jun'
        if x in d2["Jul"]:
            return 'Jul'
        if x in d2["Aug"]:
            return 'Aug'
        if x in d2["Sep"]:
            return 'Sep'
        if x in d2["Oct"]:
            return 'Oct'
        if x in d2["Nov"]:
            return 'Nov'
        if x in d2["Dec"]:
            return 'Dec'

    def Lowerleveltps(self, x):  # Lower time period_name's
        if x == 'Year':
            return ['H1', 'H2']
        if x == 'H1':
            return ['Q1', 'Q2']
        if x == 'H2':
            return ['Q3', 'Q4']
        if x == 'Q1':
            return ['Jan', 'Feb', 'Mar']
        if x == 'Q2':
            return ['Apr', 'May', 'Jun']
        if x == 'Q3':
            return ['Jul', 'Aug', 'Sep']
        if x == 'Q4':
            return ['Oct', 'Nov', 'Dec']
        if x in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']:
            return []

    def HigherlevelTimePeriods(self, x,year): # Higher period_type's
        if set(x) == set(['W_1','W_2','W_3','W_4','W_5','W_6','W_7','W_8','W_9','W_10','W_11','W_12','W_13','W_14','W_15','W_16','W_17','W_18','W_19','W_20','W_21','W_22','W_23','W_24','W_25','W_26','W_27','W_28','W_29','W_30','W_31','W_32','W_33','W_34','W_35','W_36','W_37','W_38','W_39','W_40','W_41','W_42','W_43','W_44','W_45','W_46','W_47','W_48','W_49','W_50','W_51','W_52','W_53']):
            noofweeks = self.noofweeks(year)
            d2=dict()
            for z in noofweeks.values():
                d2[list(z)[0].title()]=[]
            for z in noofweeks.items():
                d2[list(z[1])[0].title()].append(z[0])
            return {
                "Jan": d2["Jan"],"Feb":d2["Feb"],"Mar": d2["Mar"],"Apr" : d2["Apr"],"May":d2["May"],"Jun": d2["Jun"],"Jul": d2["Jul"],
                "Aug": d2["Aug"],"Sep": d2["Sep"], "Oct": d2["Oct"],
                "Nov":d2["Nov"] ,"Dec": d2["Dec"]
                }

        if set(x) == set(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
            return { 'Q1': ['Jan', 'Feb', 'Mar'], 'Q2': ['Apr', 'May', 'Jun'], 'Q3': ['Jul', 'Aug', 'Sep'],
                     'Q4': ['Oct', 'Nov', 'Dec'] }
        if set(x) == set(['Q1', 'Q2', 'Q3', 'Q4']):
            return { 'H1': ['Q1', 'Q2'], 'H2': ['Q3', 'Q4'] }

        if set(x) == set(['H1', 'H2']):
            return { 'Year': ['H1', 'H2'] }
        if set(x) == set(['Year']):
            return { }

    def LowerlevelTimePeriods(self, x):  # Lower period_type's
        if set(x) == set(['Year']):
            return ['H1', 'H2']
        if set(x) == set(['H1', 'H2', 'Year']):
            return ['Q1', 'Q2', 'Q3', 'Q4']
        if set(x) == set(['Q1', 'Q2', 'Q3', 'Q4', 'H1', 'H2', 'Year']):
            return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        if set(x) == set(['Q1', 'Q2', 'Q3', 'Q4', 'H1', 'H2', 'Year', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
            return ['W_1','W_2','W_3','W_4','W_5','W_6','W_7','W_8','W_9','W_10','W_11','W_12','W_13','W_14','W_15','W_16','W_17','W_18','W_19','W_20','W_21','W_22','W_23','W_24','W_25','W_26','W_27','W_28','W_29','W_30','W_31','W_32','W_33','W_34','W_35','W_36','W_37','W_38','W_39','W_40','W_41','W_42','W_43','W_44','W_45','W_46','W_47','W_48','W_49','W_50','W_51','W_52','W_53']
        if set(x) == set(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec','Q1', 'Q2', 'Q3', 'Q4', 'H1', 'H2', 'Year','W_1','W_2','W_3','W_4','W_5','W_6','W_7','W_8','W_9','W_10','W_11','W_12','W_13','W_14','W_15','W_16','W_17','W_18','W_19','W_20','W_21','W_22','W_23','W_24','W_25','W_26','W_27','W_28','W_29','W_30','W_31','W_32','W_33','W_34','W_35','W_36','W_37','W_38','W_39','W_40','W_41','W_42','W_43','W_44','W_45','W_46','W_47','W_48','W_49','W_50','W_51','W_52','W_53']):
            return []

    def noofweeks(self,year):
        month={"jan":31,"feb":28,"mar":31,"apr":30,"may":31,"jun":30,"jul":31,"aug":31,"sep":30,"oct":31,"nov":30,"dec":31}
        s="W_"
        date_string = f"{year}-01-01"
        date_obj = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        day_of_week = date_obj.weekday()
        c=day_of_week+1
        d1=dict()
        d1["W_1"]=set()
        s1="W_1"
        x=set()
        x.add("jan")
        d1[s1]=x
        e=2
        for i in month.keys(): 
            for j in range(1,month[i]+1):
                if (i == "jan") and (j==1):
                    z=0 
                else:
                    if c%7==0:
                        s1=s+str(e)
                        e=e+1
                        d1[s1]=set()
                if len(d1[s1])==0:
                    d1[s1].add(i)
                else:
                    y=list(d1[s1])[0]
                    d1[s1].remove(y)
                    d1[s1].add(i)
                c=c+1
        return d1
    def noofweeks_date(self,year):
        month={"jan":31,"feb":28,"mar":31,"apr":30,"may":31,"jun":30,"jul":31,"aug":31,"sep":30,"oct":31,"nov":30,"dec":31}
        s="W_"
        date_string = f"{year}-01-01"
        date_obj = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        day_of_week = date_obj.weekday()
        c=day_of_week+1
        d1=dict()
        d1["W_1"]=set()
        s1="W_1"
        x=set()
        x.add("jan")
        d1[s1]=x
        d4 = dict()
        d4[s1]=f"{year}-jan-1"
        e=2
        for i in month.keys(): 
            for j in range(1,month[i]+1):
                if (i == "jan") and (j==1):
                    z=0 
                else:
                    if c%7==0:
                        s1=s+str(e)
                        e=e+1
                        d1[s1]=set()
                        d4[s1]=f"{year}-{i}-{j}"
                if len(d1[s1])==0:
                    d1[s1].add(i)
                else:
                    y=list(d1[s1])[0]
                    d1[s1].remove(y)
                    d1[s1].add(i)
                c=c+1  
        return d4

    def NC2(self, node, new_val, period_name, base_scenario, media_hierarchy):
        condition = (self.df['node_id'] == node) & (self.df['period_name'] == period_name)
        if (self.df.loc[condition, 'node_name'] == '').bool():
            leafnodes = eval(media_hierarchy[media_hierarchy['node_id'] == node]['leaf_nodes'].values[0])
            bas_val = self.df[condition]['spend_value'].values[0]
            for lnode in leafnodes:
                condition = (self.df['node_name'] == lnode) & (self.df['period_name'] == period_name)
                self.df.loc[condition, 'spend_value'] = self.df.loc[condition, 'spend_value'].values[
                                                            0] * new_val / bas_val
        else:
            self.df.loc[condition, 'spend_value'] = new_val

        for index, row in self.df.iterrows():
            if row['node_name'] == '' and row['period_name'] == period_name:
                condition = media_hierarchy['node_id'] == row['node_id']
                self.df.loc[index, 'spend_value'] = self.df[
                    (self.df['node_name'].isin(eval(media_hierarchy[condition]['leaf_nodes'].values[0]))) & (
                            self.df['period_name'] == period_name)]['spend_value'].sum()

        self.df = self.HigherLevelAggregationOnUpdate(period_name)
        self.df = self.LowerLevelDistributionOnUpdate(period_name, base_scenario)

        self.df['Total'] = self.df.groupby(['node_id', 'period_type'])['spend_value'].transform('sum')
        return self.df.to_dict('records')

    def HigherLevelAggregationOnUpdate(self, period_name):
        tochange = self.HigherleveltpsReturnString(period_name,2021)
        if not tochange:
            return self.df
        else:
            for index, row in self.df.iterrows():
                if row['period_name'] == tochange:
                    periods = self.Lowerleveltps(tochange)
                    condition = (self.df['node_id'] == row['node_id']) & (self.df['period_name'].isin(periods))
                    self.df.loc[index, 'spend_value'] = self.df[condition]['spend_value'].sum()
            return self.HigherLevelAggregationOnUpdate(tochange)

    def LowerLevelDistributionOnUpdate(self, period_name, week_ratio_df):
        tochange = self.Lowerleveltps(period_name)
        if not tochange:
            return self.df
        else:
            for i in tochange:
                higherlevelcol = self.HigherleveltpsReturnString(i,2021)
                child_idx = self.df[self.df['period_name'] == i].index.tolist()
                parent_idx = self.df[self.df['period_name'] == higherlevelcol].index.tolist()
                if (i in ['Q1', 'Q2', 'Q3', 'Q4', 'H1', 'H2']):
                    self.df.loc[child_idx,'spend_value'] = (self.df.loc[parent_idx,'spend_value'] / 2).values
                else:
                    self.df.loc[child_idx,'spend_value'] = (self.df.loc[parent_idx,'spend_value'] * week_ratio_df.loc[week_ratio_df['MONTH']==i, 'Week_Ratio'].reset_index(drop=True)[0]).values
                
                self.LowerLevelDistributionOnUpdate(i, week_ratio_df)
            return self.df

    def HigherLevelAggregation(self, period_type,year):
        tochange = self.HigherlevelTimePeriods(period_type,year)
        if not tochange or len(tochange.keys()) == 0:
            if len(self.df.columns)>25:
                weeks_sp=[]
                weeks_or=[]
                for i in self.df.drop(["node_id"],axis=1).columns:
                    if 'W_' in i:
                        weeks_or.append(i)
                weeks = self.noofweeks_date(year)
                for i in weeks_or:
                    weeks_sp.append(i+" "+weeks[i])
                self.df[weeks_sp]=self.df[weeks_or]
                self.df=self.df.drop(weeks_or,axis=1)
            return self.df
        else:
            for i in tochange.keys():
                self.df[i] = self.df[tochange[i]].sum(axis = 1)

            return self.HigherLevelAggregation(tochange.keys(),year)

    def LowerLevelDestribution(self, period_type, week_ratio_df,get_year):
        tochange = self.LowerlevelTimePeriods(period_type)
        if not tochange or len(tochange) == 0:
            return self.df
        else:
            for i in tochange:
                higherlevelcol = self.HigherleveltpsReturnString(i,get_year)
                if (i in ['Q1', 'Q2', 'Q3', 'Q4', 'H1', 'H2']):
                    self.df[i] = self.df[higherlevelcol] / 2
                elif "W" in i:
                    noofweeks = self.noofweeks(get_year)
                    d2=dict()
                    for z in noofweeks.values():
                        d2[list(z)[0].title()]=[]
                    for z in noofweeks.items():
                        d2[list(z[1])[0].title()].append(z[0])
                    

                    d3=dict()
                    for z in d2.keys():
                        d3[z]=len(d2[z])
                    week_dates = self.noofweeks_date(get_year)
                    j=i+' '+week_dates[i]
                    self.df[j]= self.df[higherlevelcol]/d3[higherlevelcol]
                    
                else:
                    self.df[i] = self.df[higherlevelcol] * week_ratio_df.loc[week_ratio_df['MONTH']==i, 'Week_Ratio'].reset_index(drop=True)[0]
                
                period_type.append(i)
            return self.LowerLevelDestribution(period_type, week_ratio_df,get_year)
